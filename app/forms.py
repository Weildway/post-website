from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Length, UUID

class LoginForm(FlaskForm):
    username        = StringField('username', validators=[InputRequired(), Length(min=4, max=64)])
    password        = PasswordField('password', validators=[InputRequired(), Length(min=5, max=64)])
    remember        = BooleanField('remember me')

class RegisterForm(FlaskForm):
    username        = StringField('username', validators=[InputRequired(), Length(min=4, max=64)])
    password        = PasswordField('password', validators=[InputRequired(), Length(min=5, max=64)])


class CreateForm(FlaskForm):
    sender          = StringField('Sender', validators=[InputRequired(), Length(min=4, max=64)])
    receiver        = StringField('Receiver', validators=[InputRequired(), Length(min=4, max=64)])

    sender_index    = StringField('Sender index', validators=[InputRequired(), Length(min=6, max=6)])
    receiver_index  = StringField('Receiver index', validators=[InputRequired(), Length(min=6, max=6)])

    sender_addr     = StringField('Sender addr', validators=[InputRequired(), Length(min=4, max=64)])
    receiver_addr   = StringField('Receiver addr', validators=[InputRequired(), Length(min=4, max=64)])

    pkg_name        = TextAreaField('Package name', validators=[InputRequired(), Length(min=4, max=64)])
    submit_button   = SubmitField('Submit', render_kw={'style': 'width: 100%'})


class UpdateForm(FlaskForm):
    sender          = StringField('', validators=[InputRequired(), Length(min=4, max=64)])
    receiver        = StringField('', validators=[InputRequired(), Length(min=4, max=64)])

    sender_index    = StringField('', validators=[InputRequired(), Length(min=6, max=6)])
    receiver_index  = StringField('', validators=[InputRequired(), Length(min=6, max=6)])

    sender_addr     = StringField('', validators=[InputRequired(), Length(min=4, max=64)])
    receiver_addr   = StringField('', validators=[InputRequired(), Length(min=4, max=64)])

    pkg_name        = StringField('', validators=[InputRequired(), Length(min=4, max=64)])
    pkg_status      = StringField('', validators=[InputRequired(), Length(min=1, max=64)])
    submit_button   = SubmitField('Save', render_kw={'style': 'width: 20%; float: right;'})


class TrackingForm(FlaskForm):
    order_code = StringField(   '',
                                validators=[InputRequired(), UUID()],
                                render_kw={'style': 'height: 3em', 'class': 'form-control form-control-lg', 'placeholder': 'Order code'})

    submit_button = SubmitField('Track', render_kw={'style': 'width: 100%'})