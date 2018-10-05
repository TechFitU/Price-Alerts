from wtforms.widgets import TextInput, PasswordInput


class MyTextInput(TextInput):
    def __init__(self, error_class=u'is-invalid'):
        super(MyTextInput, self).__init__()
        self.error_class = error_class

    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % (self.error_class, c)
        return super(MyTextInput, self).__call__(field, **kwargs)


class CustomPasswordInput(PasswordInput):
    def __init__(self, error_class=u'is-invalid'):
        super(CustomPasswordInput, self).__init__()
        self.error_class = error_class

    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % (self.error_class, c)
        return super(CustomPasswordInput, self).__call__(field, **kwargs)
