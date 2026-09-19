from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.models import Item, Transfer, ItemStatus, TransferStatus

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('main/dashboard.html', **_dashboard_context())
    from flask import redirect, url_for
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html', **_dashboard_context())


def _dashboard_context():
    if current_user.is_admin:
        items = Item.query.all()
        pending = Transfer.query.filter_by(status=TransferStatus.PENDING.value).all()
    else:
        items = Item.query.filter_by(current_center_id=current_user.resource_center_id).all()
        pending = Transfer.query.filter(
            ((Transfer.to_center_id == current_user.resource_center_id) |
             (Transfer.from_center_id == current_user.resource_center_id)) &
            (Transfer.status.in_([TransferStatus.PENDING.value, TransferStatus.APPROVED.value]))
        ).all()

    stats = {
        'total_items': len(items),
        'active_items': len([i for i in items if i.status == ItemStatus.ACTIVE.value]),
        'decommissioned_items': len([i for i in items if i.status == ItemStatus.DECOMMISSIONED.value]),
        'pending_transfers': len(pending),
    }
    return {
        'stats': stats,
        'items': items[:8],
        'pending_transfers': pending[:5],
    }


@main_bp.route('/api/stats')
@login_required
def api_stats():
    if current_user.is_admin:
        items = Item.query.all()
    else:
        items = Item.query.filter_by(current_center_id=current_user.resource_center_id).all()

    by_category = {}
    for item in items:
        by_category[item.category.name] = by_category.get(item.category.name, 0) + 1

    return jsonify({
        'total': len(items),
        'active': len([i for i in items if i.status == ItemStatus.ACTIVE.value]),
        'decommissioned': len([i for i in items if i.status == ItemStatus.DECOMMISSIONED.value]),
        'by_category': by_category,
    })