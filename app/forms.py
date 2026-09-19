from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField, TextAreaField,
    IntegerField, FloatField, DateField, SubmitField, ValidationError
)
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Sign in')


class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Optional(), Length(max=120)])
    quantity = IntegerField('Quantity', default=1, validators=[NumberRange(min=1)])
    condition = SelectField(
        'Condition',
        choices=[('New', 'New'), ('Good', 'Good'), ('Fair', 'Fair'), ('Poor', 'Poor')],
        validators=[Optional()],
    )
    acquisition_type = SelectField(
        'Acquisition Type',
        choices=[('donated', 'Donated'), ('purchased', 'Purchased')],
        validators=[DataRequired()],
    )
    organization_id = SelectField(
        'Donor Organization',
        coerce=int,
        choices=[],  # populated in the view
        validators=[Optional()],  # conditional — see validate_organization_id below
    )
    purchase_price = FloatField('Purchase Price', validators=[Optional()])
    purchase_date = DateField('Purchase Date', validators=[Optional()])
    submit = SubmitField('Save')

    def validate_organization_id(self, field):
        """If the item is donated, an organization must be selected."""
        if self.acquisition_type.data == 'donated':
            if not field.data or field.data == 0:
                raise ValidationError(
                    'Please select the organization that donated this item.'
                )


class DecommissionForm(FlaskForm):
    reason = TextAreaField('Reason for decommissioning', validators=[DataRequired()])
    submit = SubmitField('Decommission')


class TransferForm(FlaskForm):
    to_center_id = SelectField('Destination Center', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit Transfer Request')


class RejectTransferForm(FlaskForm):
    reason = TextAreaField('Rejection Reason', validators=[DataRequired()])
    submit = SubmitField('Reject')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    is_admin = BooleanField('Administrator')
    resource_center_id = SelectField('Resource Center', coerce=int, validators=[Optional()])
    submit = SubmitField('Create User')



from app.data.subcounties import SUBCounty_WARDS


class ResourceCenterForm(FlaskForm):
    name = StringField('Center Name', validators=[DataRequired(), Length(max=120)])

    # Cascading dropdowns — choices are loaded in the view
    subcounty = SelectField(
        'Subcounty',
        choices=[],  # populated in the route
        validators=[Optional()],
    )
    ward = SelectField(
        'Ward',
        choices=[],  # populated in the route
        validators=[Optional()],
    )

    location = StringField('Location / Address', validators=[Optional(), Length(max=200)])

    latitude = FloatField(
        'Latitude',
        validators=[Optional(), NumberRange(min=-90, max=90)],
        description='Between -90 and 90. Leave blank to fill later.',
    )
    longitude = FloatField(
        'Longitude',
        validators=[Optional(), NumberRange(min=-180, max=180)],
        description='Between -180 and 180. Leave blank to fill later.',
    )

    contact_person = StringField('Contact Person', validators=[Optional()])
    contact_email = StringField('Contact Email', validators=[Optional(), Email()])
    contact_phone = StringField('Contact Phone', validators=[Optional()])

    submit = SubmitField('Save')


class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save')


class OrganizationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    contact_person = StringField('Contact Person')
    contact_email = StringField('Contact Email', validators=[Optional(), Email()])
    contact_phone = StringField('Contact Phone')
    address = TextAreaField('Address')
    submit = SubmitField('Save')