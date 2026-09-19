from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app import db
from app.models import Item, Transfer, ResourceCenter, ItemStatus, TransferStatus
from app.forms import TransferForm, RejectTransferForm
from app.decorators import admin_required

transfers_bp = Blueprint('transfers', __name__)


def _user_can_view(transfer):
    if current_user.is_admin:
        return True
    return (
        transfer.from_center_id == current_user.resource_center_id
        or transfer.to_center_id == current_user.resource_center_id
    )


@transfers_bp.route('/')
@login_required
def list_transfers():
    if current_user.is_admin:
        transfers = Transfer.query.order_by(Transfer.sent_date.desc()).all()
    else:
        transfers = (
            Transfer.query.filter(
                (Transfer.from_center_id == current_user.resource_center_id)
                | (Transfer.to_center_id == current_user.resource_center_id)
            )
            .order_by(Transfer.sent_date.desc())
            .all()
        )
    return render_template('transfers/list.html', transfers=transfers)


@transfers_bp.route('/<int:transfer_id>')
@login_required
def view_transfer(transfer_id):
    transfer = Transfer.query.get_or_404(transfer_id)
    if not _user_can_view(transfer):
        abort(403)
    reject_form = RejectTransferForm()
    return render_template('transfers/view.html', transfer=transfer, reject_form=reject_form)


@transfers_bp.route('/new/<int:item_id>', methods=['GET', 'POST'])
@login_required
def new_transfer(item_id):
    item = Item.query.get_or_404(item_id)

    if item.current_center_id != current_user.resource_center_id and not current_user.is_admin:
        abort(403)

    if item.status != ItemStatus.ACTIVE.value:
        flash('Only active items can be transferred.', 'danger')
        return redirect(url_for('items.view_item', item_id=item.id))

    form = TransferForm()
    form.to_center_id.choices = [
        (c.id, c.name)
        for c in ResourceCenter.query.filter(
            ResourceCenter.id != item.current_center_id,
            ResourceCenter.is_active == True,  # noqa: E712
        ).order_by(ResourceCenter.name)
    ]

    if form.validate_on_submit():
        try:
            transfer = Transfer(
                item_id=item.id,
                from_center_id=item.current_center_id,
                to_center_id=form.to_center_id.data,
                sent_by_id=current_user.id,
                status=TransferStatus.PENDING.value,
                notes=form.notes.data,
            )
            item.status = ItemStatus.PENDING_TRANSFER.value
            db.session.add(transfer)
            db.session.commit()
            flash('Transfer request submitted for approval.', 'success')
            return redirect(url_for('transfers.list_transfers'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating transfer: {exc}', 'danger')

    return render_template('transfers/new.html', form=form, item=item)


@transfers_bp.route('/<int:transfer_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_transfer(transfer_id):
    transfer = Transfer.query.get_or_404(transfer_id)
    if transfer.status != TransferStatus.PENDING.value:
        flash('Only pending transfers can be approved.', 'warning')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))

    transfer.status = TransferStatus.APPROVED.value
    transfer.approved_by_id = current_user.id
    transfer.approved_date = datetime.utcnow()
    db.session.commit()
    flash('Transfer approved. Awaiting receipt at destination.', 'success')
    return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))


@transfers_bp.route('/<int:transfer_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_transfer(transfer_id):
    transfer = Transfer.query.get_or_404(transfer_id)
    form = RejectTransferForm()

    if transfer.status != TransferStatus.PENDING.value:
        flash('Only pending transfers can be rejected.', 'warning')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))

    if form.validate_on_submit():
        transfer.status = TransferStatus.REJECTED.value
        transfer.approved_by_id = current_user.id
        transfer.approved_date = datetime.utcnow()
        transfer.rejection_reason = form.reason.data
        transfer.item.status = ItemStatus.ACTIVE.value
        db.session.commit()
        flash('Transfer rejected.', 'info')
    else:
        flash('Rejection reason is required.', 'danger')

    return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))


@transfers_bp.route('/<int:transfer_id>/receive', methods=['POST'])
@login_required
def receive_transfer(transfer_id):
    transfer = Transfer.query.get_or_404(transfer_id)

    if transfer.to_center_id != current_user.resource_center_id and not current_user.is_admin:
        abort(403)

    if transfer.status != TransferStatus.APPROVED.value:
        flash('Transfer must be approved before receiving.', 'warning')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))

    try:
        transfer.status = TransferStatus.COMPLETED.value
        transfer.received_by_id = current_user.id
        transfer.received_date = datetime.utcnow()

        transfer.item.current_center_id = transfer.to_center_id
        transfer.item.status = ItemStatus.ACTIVE.value
        transfer.item.received_by_id = current_user.id
        transfer.item.received_date = datetime.utcnow()
        db.session.commit()
        flash('Transfer completed successfully.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error receiving transfer: {exc}', 'danger')

    return redirect(url_for('transfers.view_transfer', transfer_id=transfer.id))