from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user

from app import db
from app.models import User, ResourceCenter, Category, Organization, Item, ItemStatus
from app.forms import UserForm, ResourceCenterForm, CategoryForm, OrganizationForm, EditUserForm, ResetUserPasswordForm
from app.decorators import admin_required


from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

from app.data.subcounties import SUBCounty_WARDS, SUBCounty_NAMES


def _populate_center_choices(form, selected_subcounty=None, selected_ward=None):
    """Wire up cascading subcounty → ward dropdowns."""
    form.subcounty.choices = [('', '-- Select Subcounty --')] + [
        (s, s) for s in SUBCounty_NAMES
    ]
    if selected_subcounty and selected_subcounty in SUBCounty_WARDS:
        wards = SUBCounty_WARDS[selected_subcounty]
    else:
        wards = []
    form.ward.choices = [('', '-- Select Ward --')] + [(w, w) for w in wards]

# ---------------- Users ----------------
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = UserForm()
    form.resource_center_id.choices = [(0, '-- None --')] + [
        (c.id, c.name) for c in ResourceCenter.query.order_by(ResourceCenter.name)
    ]

    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_admin=form.is_admin.data,
                resource_center_id=form.resource_center_id.data or None,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/new_user.html', form=form)

# ---------------- Users: edit / reset password / toggle ----------------

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.resource_center_id.choices = [(0, '-- None --')] + [
        (c.id, c.name) for c in ResourceCenter.query.order_by(ResourceCenter.name)
    ]

    # Normalize the "no center" choice: 0 -> None
    if form.validate_on_submit():
        # Prevent admins from demoting themselves (avoid lockout)
        if user.id == current_user.id and not form.is_admin.data:
            flash('You cannot remove your own administrator privileges.', 'warning')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        # Prevent duplicate usernames / emails
        if User.query.filter(User.username == form.username.data, User.id != user.id).first():
            flash('Another user already has that username.', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user)

        if User.query.filter(User.email == form.email.data, User.id != user.id).first():
            flash('Another user already has that email.', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user)

        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        user.resource_center_id = form.resource_center_id.data or None
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetUserPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(f'Password reset for {user.username}.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/reset_user_password.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent self-deactivation (would lock yourself out)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()
    state = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {state}.', 'success')
    return redirect(url_for('admin.users'))


# ---------------- Categories ----------------
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    all_categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=all_categories)


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data).first():
            flash('Category already exists.', 'warning')
        else:
            db.session.add(Category(name=form.name.data, description=form.description.data))
            db.session.commit()
            flash('Category created.', 'success')
            return redirect(url_for('admin.categories'))
    return render_template('admin/new_category.html', form=form)


# ---------------- Organizations ----------------
@admin_bp.route('/organizations')
@login_required
@admin_required
def organizations():
    orgs = Organization.query.order_by(Organization.name).all()
    return render_template('admin/organizations.html', organizations=orgs)


@admin_bp.route('/organizations/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        db.session.add(Organization(
            name=form.name.data,
            contact_person=form.contact_person.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
            address=form.address.data,
        ))
        db.session.commit()
        flash('Organization created.', 'success')
        return redirect(url_for('admin.organizations'))
    return render_template('admin/new_organization.html', form=form)


@admin_bp.route('/centers')
@login_required
@admin_required
def centers():
    # Per-center counts in one query:
    #   - total items
    #   - active items
    rows = (
        db.session.query(
            Item.current_center_id.label('center_id'),
            func.count(Item.id).label('total'),
            func.sum(
                db.case(
                    (Item.status == ItemStatus.ACTIVE.value, 1),
                    else_=0,
                )
            ).label('active'),
        )
        .group_by(Item.current_center_id)
        .all()
    )

    counts = {
        r.center_id: {'total': r.total, 'active': int(r.active or 0)}
        for r in rows
    }

    all_centers = ResourceCenter.query.order_by(ResourceCenter.name).all()

    return render_template(
        'admin/centers.html',
        centers=all_centers,
        counts=counts,
    )


# @admin_bp.route('/centers/new', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def new_center():
#     form = ResourceCenterForm()
#     if form.validate_on_submit():
#         center = ResourceCenter(
#             name=form.name.data,
#             subcounty=form.subcounty.data,
#             ward=form.ward.data,
#             location=form.location.data,
#             latitude=form.latitude.data,
#             longitude=form.longitude.data,
#             contact_person=form.contact_person.data,
#             contact_email=form.contact_email.data,
#             contact_phone=form.contact_phone.data,
#         )
#         db.session.add(center)
#         db.session.commit()
#         flash('Resource center created.', 'success')
#         return redirect(url_for('admin.centers'))
#     return render_template('admin/new_center.html', form=form)


# @admin_bp.route('/centers/<int:center_id>/edit', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def edit_center(center_id):
#     center = ResourceCenter.query.get_or_404(center_id)
#     form = ResourceCenterForm(obj=center)

#     if form.validate_on_submit():
#         center.name = form.name.data
#         center.subcounty = form.subcounty.data
#         center.ward = form.ward.data
#         center.location = form.location.data
#         center.latitude = form.latitude.data
#         center.longitude = form.longitude.data
#         center.contact_person = form.contact_person.data
#         center.contact_email = form.contact_email.data
#         center.contact_phone = form.contact_phone.data
#         db.session.commit()
#         flash('Resource center updated.', 'success')
#         return redirect(url_for('admin.centers'))
#     return render_template('admin/edit_center.html', form=form, center=center)

@admin_bp.route('/centers/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_center():
    form = ResourceCenterForm()

    # On POST, use the submitted subcounty so ward choices are populated
    submitted_subcounty = form.subcounty.data if request.method == 'POST' else None
    _populate_center_choices(form, selected_subcounty=submitted_subcounty)

    if form.validate_on_submit():
        center = ResourceCenter(
            name=form.name.data,
            subcounty=form.subcounty.data,
            ward=form.ward.data,
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            contact_person=form.contact_person.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
        )
        db.session.add(center)
        db.session.commit()
        flash('Resource center created.', 'success')
        return redirect(url_for('admin.centers'))

    return render_template('admin/new_center.html', form=form)


@admin_bp.route('/centers/<int:center_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_center(center_id):
    center = ResourceCenter.query.get_or_404(center_id)
    form = ResourceCenterForm(obj=center)

    # Determine subcounty to base ward choices on:
    # - POST: what the user just submitted
    # - GET: what's already saved
    selected_subcounty = form.subcounty.data if request.method == 'POST' else center.subcounty
    selected_ward = form.ward.data if request.method == 'POST' else center.ward
    _populate_center_choices(form, selected_subcounty, selected_ward)

    if form.validate_on_submit():
        center.name = form.name.data
        center.subcounty = form.subcounty.data
        center.ward = form.ward.data
        center.location = form.location.data
        center.latitude = form.latitude.data
        center.longitude = form.longitude.data
        center.contact_person = form.contact_person.data
        center.contact_email = form.contact_email.data
        center.contact_phone = form.contact_phone.data
        db.session.commit()
        flash('Resource center updated.', 'success')
        return redirect(url_for('admin.centers'))

    return render_template('admin/edit_center.html', form=form, center=center)

@admin_bp.route('/centers/map')
@login_required
@admin_required
def centers_map():
    """Show all centers (with coordinates) on a map."""
    centers = ResourceCenter.query.all()
    mapped = [
        {
            'id': c.id,
            'name': c.name,
            'subcounty': c.subcounty or '',
            'ward': c.ward or '',
            'location': c.location or '',
            'lat': c.latitude,
            'lng': c.longitude,
            'contact': c.contact_person or '',
            'phone': c.contact_phone or '',
            'has_coords': c.has_coordinates,
        }
        for c in centers
    ]
    return render_template('admin/centers_map.html', centers=mapped)


@admin_bp.route('/api/centers')
@login_required
def api_centers():
    """JSON feed of centers with coordinates (used by the map)."""
    centers = ResourceCenter.query.filter(
        ResourceCenter.latitude.isnot(None),
        ResourceCenter.longitude.isnot(None),
    ).all()
    return jsonify([
        {
            'id': c.id,
            'name': c.name,
            'subcounty': c.subcounty,
            'ward': c.ward,
            'location': c.location,
            'lat': c.latitude,
            'lng': c.longitude,
            'contact_person': c.contact_person,
            'contact_phone': c.contact_phone,
        }
        for c in centers
    ])

@admin_bp.route('/api/wards')
@login_required
def api_wards():
    """Return wards for a given subcounty: /admin/api/wards?subcounty=Kasarani"""
    subcounty = request.args.get('subcounty', '')
    return jsonify(SUBCounty_WARDS.get(subcounty, []))