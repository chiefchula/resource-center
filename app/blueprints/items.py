from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models import Item, Category, Organization, ItemStatus, AcquisitionType
from app.forms import ItemForm, DecommissionForm
from app.decorators import center_access_required

items_bp = Blueprint('items', __name__)


def _can_access(item):
    return current_user.is_admin or item.current_center_id == current_user.resource_center_id


@items_bp.route('/')
@login_required
def list_items():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    status = request.args.get('status')
    search = request.args.get('q', '').strip()

    query = Item.query
    if not current_user.is_admin:
        query = query.filter_by(current_center_id=current_user.resource_center_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%'))

    items = query.order_by(Item.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'items/list.html',
        items=items,
        categories=categories,
        current_category=category_id,
        current_status=status,
        search=search,
    )


@items_bp.route('/new', methods=['GET', 'POST'])
@login_required
@center_access_required
def new_item():
    form = ItemForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name)]
    form.organization_id.choices = [(0, '-- Select --')] + [
        (o.id, o.name) for o in Organization.query.order_by(Organization.name)
    ]

    if form.validate_on_submit():
        try:
            item = Item(
                name=form.name.data,
                description=form.description.data,
                category_id=form.category_id.data,
                serial_number=form.serial_number.data or None,
                quantity=form.quantity.data or 1,
                condition=form.condition.data,
                acquisition_type=form.acquisition_type.data,
                organization_id=form.organization_id.data or None
                if form.acquisition_type.data == AcquisitionType.DONATED.value else None,
                purchase_price=form.purchase_price.data
                if form.acquisition_type.data == AcquisitionType.PURCHASED.value else None,
                purchase_date=form.purchase_date.data
                if form.acquisition_type.data == AcquisitionType.PURCHASED.value else None,
                current_center_id=current_user.resource_center_id,
                received_by_id=current_user.id,
                status=ItemStatus.ACTIVE.value,
            )
            db.session.add(item)
            db.session.commit()
            flash('Item registered successfully.', 'success')
            return redirect(url_for('items.view_item', item_id=item.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating item: {exc}', 'danger')

    return render_template('items/new.html', form=form)


@items_bp.route('/<int:item_id>')
@login_required
def view_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not _can_access(item):
        abort(403)
    decommission_form = DecommissionForm()
    return render_template('items/view.html', item=item, decommission_form=decommission_form)


@items_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not _can_access(item):
        abort(403)

    form = ItemForm(obj=item)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name)]
    form.organization_id.choices = [(0, '-- Select --')] + [
        (o.id, o.name) for o in Organization.query.order_by(Organization.name)
    ]

    if form.validate_on_submit():
        try:
            item.name = form.name.data
            item.description = form.description.data
            item.category_id = form.category_id.data
            item.serial_number = form.serial_number.data or None
            item.quantity = form.quantity.data or 1
            item.condition = form.condition.data
            item.acquisition_type = form.acquisition_type.data

            if form.acquisition_type.data == AcquisitionType.DONATED.value:
                item.organization_id = form.organization_id.data or None
                item.purchase_price = None
                item.purchase_date = None
            else:
                item.organization_id = None
                item.purchase_price = form.purchase_price.data
                item.purchase_date = form.purchase_date.data

            db.session.commit()
            flash('Item updated successfully.', 'success')
            return redirect(url_for('items.view_item', item_id=item.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Error updating item: {exc}', 'danger')

    return render_template('items/edit.html', form=form, item=item)


@items_bp.route('/<int:item_id>/decommission', methods=['POST'])
@login_required
def decommission_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not _can_access(item):
        abort(403)

    if item.status == ItemStatus.DECOMMISSIONED.value:
        flash('Item is already decommissioned.', 'warning')
        return redirect(url_for('items.view_item', item_id=item.id))

    form = DecommissionForm()
    if form.validate_on_submit():
        try:
            item.status = ItemStatus.DECOMMISSIONED.value
            item.decommission_date = datetime.utcnow()
            item.decommission_reason = form.reason.data
            item.decommissioned_by_id = current_user.id
            db.session.commit()
            flash('Item decommissioned successfully.', 'success')
        except Exception as exc:
            db.session.rollback()
            flash(f'Error decommissioning item: {exc}', 'danger')
    else:
        flash('Reason is required.', 'danger')

    return redirect(url_for('items.view_item', item_id=item.id))