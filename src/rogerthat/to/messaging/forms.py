# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.7@@

import itertools
import urllib2

from mcfw.consts import MISSING
from mcfw.properties import azzert, unicode_property, long_property, typed_property, unicode_list_property, get_members
from mcfw.utils import Enum
from rogerthat.models.properties.forms import Widget, TextLine, TextBlock, AutoComplete, SingleSelect, MultiSelect, \
    Choice, Form, SingleSlider, RangeSlider, WidgetResult, UnicodeWidgetResult, UnicodeListWidgetResult, \
    LongWidgetResult, LongListWidgetResult, FloatWidgetResult, FloatListWidgetResult, DateSelect, PhotoUpload, \
    GPSLocation, LocationWidgetResult, MyDigiPass, MyDigiPassWidgetResult, AdvancedOrderWidgetResult, AdvancedOrder, \
    AdvancedOrderItem, AdvancedOrderCategory, FriendSelect, Sign, TextWidget, SignWidgetResult, Oauth, Pay, \
    PaymentMethod, PayWidgetResult, BasePaymentMethod, OpenIdWidgetResult, OpenId
from rogerthat.to import WIDGET_MAPPING, WIDGET_TO_MAPPING, WIDGET_RESULT_TO_MAPPING, TO
from rogerthat.to.messaging import BaseMessageTO, NewMessageResponseTO, AckMessageResponseTO, MemberStatusTO, \
    BaseRootMessageTO, MessageTO


def _replace(replace_empty_values_by_missing, value):
    return MISSING if replace_empty_values_by_missing and value is None else value


class FormTO(object):
    POSITIVE = Form.POSITIVE
    NEGATIVE = Form.NEGATIVE
    type = unicode_property('1')  # @ReservedAssignment
    widget = typed_property('2', Widget, False, subtype_attr_name="type", subtype_mapping=WIDGET_TO_MAPPING)
    positive_button = unicode_property('3')
    negative_button = unicode_property('4')
    positive_confirmation = unicode_property('5')
    negative_confirmation = unicode_property('6')
    positive_button_ui_flags = long_property('7')
    negative_button_ui_flags = long_property('8')
    javascript_validation = unicode_property('9', default=None)

    @staticmethod
    def fromFormMessage(formMessage):
        w_descr = WIDGET_MAPPING[formMessage.form.type]
        to = w_descr.form_to_type()
        to.type = formMessage.form.type
        form_result = None
        for memberStatus in formMessage.memberStatusses:
            if formMessage.members[memberStatus.index] != formMessage.sender and memberStatus.form_result is not None:
                form_result = memberStatus.form_result.result
                break

        to.widget = w_descr.to_type.fromWidget(formMessage.form.widget, form_result)
        to.javascript_validation = formMessage.form.javascript_validation
        for btn in formMessage.buttons:
            confirmation = None
            if btn.action:
                scheme, _, _, _, _, _ = urllib2.urlparse.urlparse(btn.action)
                confirmation = btn.action[len("%s://" % scheme):]
            if btn.id == Form.POSITIVE:
                to.positive_button = btn.caption
                to.positive_button_ui_flags = btn.ui_flags
                to.positive_confirmation = confirmation
            elif btn.id == Form.NEGATIVE:
                to.negative_button = btn.caption
                to.negative_button_ui_flags = btn.ui_flags
                to.negative_confirmation = confirmation
        return to


class FormMessageTO(BaseMessageTO):
    form = typed_property('51', FormTO, False)
    member = typed_property('52', MemberStatusTO, False)

    @staticmethod
    def fromFormMessage(formMessage):
        w_descr = WIDGET_MAPPING[formMessage.form.type]
        to = BaseMessageTO._populateTO(
            formMessage, w_descr.fm_to_type(), formMessage.members[formMessage.memberStatusses[0].index])
        to.form = w_descr.form_to_type.fromFormMessage(formMessage)
        if getattr(to.form.widget, 'unit', None):
            to.form.widget.unit = to.form.widget.unit.replace("%", "%%")
        to.member = MemberStatusTO.fromMessageMemberStatus(formMessage, formMessage.memberStatusses[0])
        return to


class WebFormMessageTO(MessageTO):
    form = typed_property('101', FormTO, False)

    @staticmethod
    def fromMessage(fm, thread_size=0):
        wfmTO = WebFormMessageTO()
        wfmTO.__dict__.update(MessageTO.fromMessage(fm, None).__dict__)
        wfmTO.form = WIDGET_MAPPING[fm.form.type].form_to_type.fromFormMessage(fm)
        wfmTO.thread_size = thread_size
        return wfmTO


class RootFormMessageTO(WebFormMessageTO, BaseRootMessageTO):

    @staticmethod
    def fromFormMessage(fm):
        from rogerthat.models import FormMessage
        azzert(isinstance(fm, FormMessage))
        rm = RootFormMessageTO()
        rm.__dict__.update(WebFormMessageTO.fromMessage(fm).__dict__)
        rm.messages = list()
        rm.message_type = fm.TYPE
        return rm


class NewWebFormMessageRequestTO(object):
    message = typed_property('1', WebFormMessageTO, False)


class ChoiceTO(Choice):
    pass


class TextWidgetTO(object):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.max_chars = widget.max_chars
        to.place_holder = widget.place_holder
        to.value = form_result.value if form_result else widget.value
        to.keyboard_type = widget.keyboard_type or TextWidget.keyboard_type.default
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.max_chars = widget_sub.maxChars
        to.place_holder = _replace(replace_empty_values_by_missing, _unicode(widget_sub.placeholder))
        to.value = _replace(replace_empty_values_by_missing, _unicode(widget_sub.value))
        if replace_empty_values_by_missing and widget_sub.keyboardType is None:
            to.keyboard_type = MISSING
        elif not widget_sub.keyboardType:
            to.keyboard_type = TextWidget.keyboard_type.default
        else:
            to.keyboard_type = _unicode(widget_sub.keyboardType.lower())
        return to


class TextLineTO(TextWidgetTO, TextLine):
    pass


def _unicode(val):
    if val is None:
        return None
    else:
        return unicode(val)


class TextLineFormTO(FormTO):
    widget = typed_property('2', TextLineTO, False)


class TextLineFormMessageTO(FormMessageTO):
    form = typed_property('51', TextLineFormTO, False)


class NewTextLineFormRequestTO(object):
    form_message = typed_property('1', TextLineFormMessageTO, False)


class NewTextLineFormResponseTO(NewMessageResponseTO):
    pass


class TextBlockTO(TextWidgetTO, TextBlock):
    pass


class TextBlockFormTO(FormTO):
    widget = typed_property('2', TextBlockTO, False)


class TextBlockFormMessageTO(FormMessageTO):
    form = typed_property('51', TextBlockFormTO, False)


class NewTextBlockFormRequestTO(object):
    form_message = typed_property('1', TextBlockFormMessageTO, False)


class NewTextBlockFormResponseTO(NewMessageResponseTO):
    pass


class AutoCompleteTO(TextWidgetTO, AutoComplete):
    choices = unicode_list_property('151')

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = super(AutoCompleteTO, cls).fromWidget(widget, form_result)
        to.choices = list(widget.suggestions)  # supported by phones
        to.suggestions = list()  # not supported by phones
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = super(AutoCompleteTO, cls).fromWidgetXmlSub(widget_sub, replace_empty_values_by_missing)
        to.choices = [_unicode(s.value) for s in widget_sub.suggestion]  # supported by phones
        to.suggestions = list()  # not supported by phones
        return to


class AutoCompleteFormTO(FormTO):
    widget = typed_property('2', AutoCompleteTO, False)


class AutoCompleteFormMessageTO(FormMessageTO):
    form = typed_property('51', AutoCompleteFormTO, False)


class NewAutoCompleteFormRequestTO(object):
    form_message = typed_property('1', AutoCompleteFormMessageTO, False)


class NewAutoCompleteFormResponseTO(NewMessageResponseTO):
    pass


class FriendSelectTO(FriendSelect):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.selection_required = widget.selection_required
        to.multi_select = widget.multi_select
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.selection_required = _replace(replace_empty_values_by_missing, widget_sub.selectionRequired)
        to.multi_select = _replace(replace_empty_values_by_missing, widget_sub.multiSelect)
        return to


class FriendSelectFormTO(FormTO):
    widget = typed_property('2', FriendSelectTO, False)


class FriendSelectFormMessageTO(FormMessageTO):
    form = typed_property('51', FriendSelectFormTO, False)


class NewFriendSelectFormRequestTO(object):
    form_message = typed_property('1', FriendSelectFormMessageTO, False)


class NewFriendSelectFormResponseTO(NewMessageResponseTO):
    pass


class SingleSelectTO(SingleSelect):
    choices = typed_property('51', ChoiceTO, True)

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.value = form_result.value if form_result else widget.value
        to.choices = [ChoiceTO(label=c.label, value=c.value) for c in widget.choices]
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.value = _replace(replace_empty_values_by_missing, _unicode(widget_sub.value))
        to.choices = [ChoiceTO(label=_unicode(c.label), value=_unicode(c.value)) for c in widget_sub.choice]
        return to


class SingleSelectFormTO(FormTO):
    widget = typed_property('2', SingleSelectTO, False)


class SingleSelectFormMessageTO(FormMessageTO):
    form = typed_property('51', SingleSelectFormTO, False)


class NewSingleSelectFormRequestTO(object):
    form_message = typed_property('1', SingleSelectFormMessageTO, False)


class NewSingleSelectFormResponseTO(NewMessageResponseTO):
    pass


class MultiSelectTO(MultiSelect):
    choices = typed_property('51', ChoiceTO, True)

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.values = form_result.values if form_result else widget.values
        to.choices = [ChoiceTO(label=c.label, value=c.value) for c in widget.choices]
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.values = [_unicode(v.value) for v in widget_sub.value]
        to.choices = [ChoiceTO(label=_unicode(c.label), value=_unicode(c.value)) for c in widget_sub.choice]
        return to


class MultiSelectFormTO(FormTO):
    widget = typed_property('2', MultiSelectTO, False)


class MultiSelectFormMessageTO(FormMessageTO):
    form = typed_property('51', MultiSelectFormTO, False)


class NewMultiSelectFormRequestTO(object):
    form_message = typed_property('1', MultiSelectFormMessageTO, False)


class NewMultiSelectFormResponseTO(NewMessageResponseTO):
    pass


class DateSelectTO(DateSelect):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.date = form_result.value if form_result else (widget.date if widget.has_date else 0)
        to.has_date = bool(form_result) or widget.has_date
        to.has_max_date = widget.has_max_date
        to.has_min_date = widget.has_min_date
        to.max_date = widget.max_date if widget.has_max_date else 0
        to.min_date = widget.min_date if widget.has_min_date else 0
        to.minute_interval = widget.minute_interval
        to.mode = widget.mode
        to.unit = widget.unit
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        EMPTY_DATE = MISSING if replace_empty_values_by_missing else 0
        to = cls()
        to.has_date = widget_sub.date is not None
        to.has_max_date = widget_sub.maxDate is not None
        to.has_min_date = widget_sub.minDate is not None
        to.date = widget_sub.date if to.has_date else EMPTY_DATE
        to.max_date = widget_sub.maxDate if to.has_max_date else EMPTY_DATE
        to.min_date = widget_sub.minDate if to.has_min_date else EMPTY_DATE
        to.minute_interval = _replace(replace_empty_values_by_missing, widget_sub.minuteInterval)
        to.mode = _replace(replace_empty_values_by_missing, _unicode(widget_sub.mode))
        to.unit = _replace(replace_empty_values_by_missing, _unicode(widget_sub.unit))
        return to


class DateSelectFormTO(FormTO):
    widget = typed_property('2', DateSelectTO, False)


class DateSelectFormMessageTO(FormMessageTO):
    form = typed_property('51', DateSelectFormTO, False)


class NewDateSelectFormRequestTO(object):
    form_message = typed_property('1', DateSelectFormMessageTO, False)


class NewDateSelectFormResponseTO(NewMessageResponseTO):
    pass


class SingleSliderTO(SingleSlider):

    def __init__(self):
        self.precision = MISSING
        self.step = MISSING
        self.unit = MISSING
        self.value = MISSING

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.max = widget.max
        to.min = widget.min
        to.precision = widget.precision
        to.step = widget.step
        to.unit = widget.unit
        to.value = form_result.value if form_result else widget.value
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.max = widget_sub.max
        to.min = widget_sub.min
        to.precision = _replace(replace_empty_values_by_missing, widget_sub.precision)
        to.step = _replace(replace_empty_values_by_missing, widget_sub.step)
        to.unit = _replace(replace_empty_values_by_missing, _unicode(widget_sub.unit))
        to.value = _replace(replace_empty_values_by_missing, widget_sub.value)
        return to


class SingleSliderFormTO(FormTO):
    widget = typed_property('2', SingleSliderTO, False)


class SingleSliderFormMessageTO(FormMessageTO):
    form = typed_property('51', SingleSliderFormTO, False)


class NewSingleSliderFormRequestTO(object):
    form_message = typed_property('1', SingleSliderFormMessageTO, False)


class NewSingleSliderFormResponseTO(NewMessageResponseTO):
    pass


class RangeSliderTO(RangeSlider):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.low_value = form_result.values[0] if form_result else widget.low_value
        to.high_value = form_result.values[1] if form_result else widget.high_value
        to.max = widget.max
        to.min = widget.min
        to.precision = widget.precision
        to.step = widget.step
        to.unit = widget.unit
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.max = widget_sub.max
        to.min = widget_sub.min
        to.precision = _replace(replace_empty_values_by_missing, widget_sub.precision)
        to.step = _replace(replace_empty_values_by_missing, widget_sub.step)
        to.unit = _replace(replace_empty_values_by_missing, _unicode(widget_sub.unit))
        to.low_value = _replace(replace_empty_values_by_missing, widget_sub.lowValue)
        to.high_value = _replace(replace_empty_values_by_missing, widget_sub.highValue)
        return to


class RangeSliderFormTO(FormTO):
    widget = typed_property('2', RangeSliderTO, False)


class RangeSliderFormMessageTO(FormMessageTO):
    form = typed_property('51', RangeSliderFormTO, False)


class NewRangeSliderFormRequestTO(object):
    form_message = typed_property('1', RangeSliderFormMessageTO, False)


class NewRangeSliderFormResponseTO(NewMessageResponseTO):
    pass


class PhotoUploadTO(PhotoUpload):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.quality = widget.quality
        to.gallery = widget.gallery
        to.camera = widget.camera
        to.ratio = widget.ratio
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.quality = _replace(replace_empty_values_by_missing, _unicode(widget_sub.quality))
        to.gallery = _replace(replace_empty_values_by_missing, widget_sub.gallery)
        to.camera = _replace(replace_empty_values_by_missing, widget_sub.camera)
        to.ratio = _replace(replace_empty_values_by_missing, _unicode(widget_sub.ratio))
        return to


class PhotoUploadFormTO(FormTO):
    widget = typed_property('2', PhotoUploadTO, False)


class PhotoUploadFormMessageTO(FormMessageTO):
    form = typed_property('51', PhotoUploadFormTO, False)


class NewPhotoUploadFormRequestTO(object):
    form_message = typed_property('1', PhotoUploadFormMessageTO, False)


class NewPhotoUploadFormResponseTO(NewMessageResponseTO):
    pass


class GPSLocationTO(GPSLocation):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.gps = widget.gps
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.gps = _replace(replace_empty_values_by_missing, widget_sub.gps)
        return to


class GPSLocationFormTO(FormTO):
    widget = typed_property('2', GPSLocationTO, False)


class GPSLocationFormMessageTO(FormMessageTO):
    form = typed_property('51', GPSLocationFormTO, False)


class NewGPSLocationFormRequestTO(object):
    form_message = typed_property('1', GPSLocationFormMessageTO, False)


class NewGPSLocationFormResponseTO(NewMessageResponseTO):
    pass


class MyDigiPassTO(MyDigiPass):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.scope = widget.scope
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.scope = _replace(replace_empty_values_by_missing, _unicode(widget_sub.scope))
        return to


class MyDigiPassFormTO(FormTO):
    widget = typed_property('2', MyDigiPassTO, False)


class MyDigiPassFormMessageTO(FormMessageTO):
    form = typed_property('51', MyDigiPassFormTO, False)


class NewMyDigiPassFormRequestTO(object):
    form_message = typed_property('1', MyDigiPassFormMessageTO, False)


class NewMyDigiPassFormResponseTO(NewMessageResponseTO):
    pass


class OpenIdProvider(Enum):
    ITSME = u'itsme'


class OpenIdTO(OpenId):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.provider = widget.provider
        to.scope = widget.scope
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.provider = _replace(replace_empty_values_by_missing, _unicode(widget_sub.provider))
        to.scope = _replace(replace_empty_values_by_missing, _unicode(widget_sub.scope))
        return to


class OpenIdFormTO(FormTO):
    widget = typed_property('2', OpenIdTO)  # type: OpenIdTO


class OpenIdFormMessageTO(FormMessageTO):
    form = typed_property('51', OpenIdFormTO)  # type: OpenIdFormTO


class NewOpenIdFormRequestTO(TO):
    form_message = typed_property('1', OpenIdFormMessageTO)


class NewOpenIdFormResponseTO(NewMessageResponseTO):
    pass


class AdvancedOrderItemTO(AdvancedOrderItem):
    pass


class AdvancedOrderCategoryTO(AdvancedOrderCategory):
    pass


class AdvancedOrderTO(AdvancedOrder):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.currency = widget.currency
        to.leap_time = widget.leap_time
        to.categories = []
        for c in widget.categories:
            category = AdvancedOrderCategoryTO()
            category.id = _unicode(c.id)
            category.name = _unicode(c.name)
            category.items = []
            for i in c.items:
                item = AdvancedOrderItemTO()
                item.id = i.id
                item.name = i.name
                item.description = i.description
                item.value = i.value
                item.unit = i.unit
                item.unit_price = i.unit_price
                item.has_price = i.has_price
                item.step = i.step
                item.step_unit = i.step_unit
                item.step_unit_conversion = i.step_unit_conversion if i.step_unit_conversion else 0
                item.image_url = i.image_url
                category.items.append(item)
            to.categories.append(category)
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.currency = _replace(replace_empty_values_by_missing, _unicode(widget_sub.currency))
        to.leap_time = _replace(replace_empty_values_by_missing, widget_sub.leapTime)
        to.categories = []
        for c in widget_sub.get_category():
            category = AdvancedOrderCategoryTO()
            category.id = _unicode(c.id)
            category.name = _unicode(c.name)
            category.items = []
            for i in c.get_item():
                item = AdvancedOrderItemTO()
                item.id = _unicode(i.id)
                item.name = _unicode(i.name)
                item.description = _unicode(i.description)
                item.value = i.value
                item.unit = _unicode(i.unit)
                item.unit_price = i.unitPrice
                item.has_price = i.hasPrice
                item.step = i.step
                item.step_unit = _unicode(i.stepUnit)
                item.step_unit_conversion = i.stepUnitConversion if i.stepUnitConversion else 0
                item.image_url = _unicode(i.imageUrl)
                category.items.append(item)
            to.categories.append(category)
        return to


class AdvancedOrderFormTO(FormTO):
    widget = typed_property('2', AdvancedOrderTO, False)


class AdvancedOrderFormMessageTO(FormMessageTO):
    form = typed_property('51', AdvancedOrderFormTO, False)


class NewAdvancedOrderFormRequestTO(object):
    form_message = typed_property('1', AdvancedOrderFormMessageTO, False)


class NewAdvancedOrderFormResponseTO(NewMessageResponseTO):
    pass


class SignTO(Sign):

    @classmethod
    def fromWidget(cls, widget, form_result=None):
        to = cls()
        to.payload = widget.payload
        to.caption = widget.caption
        to.algorithm = widget.algorithm
        to.key_name = widget.key_name
        to.index = widget.index
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.payload = _replace(replace_empty_values_by_missing, _unicode(widget_sub.payload))
        to.caption = _replace(replace_empty_values_by_missing, _unicode(widget_sub.caption))
        to.algorithm = _replace(replace_empty_values_by_missing, _unicode(widget_sub.algorithm))
        to.key_name = _replace(replace_empty_values_by_missing, _unicode(widget_sub.keyName))
        to.index = _replace(replace_empty_values_by_missing, _unicode(widget_sub.index))
        return to


class SignFormTO(FormTO):
    widget = typed_property('2', SignTO, False)


class SignFormMessageTO(FormMessageTO):
    form = typed_property('51', SignFormTO, False)


class NewSignFormRequestTO(object):
    form_message = typed_property('1', SignFormMessageTO, False)


class NewSignFormResponseTO(NewMessageResponseTO):
    pass


class OauthTO(Oauth):

    @classmethod
    def fromWidget(cls, model, form_result=None):
        to = cls()
        to.__dict__ = model.__dict__
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        to = cls()
        to.url = _replace(replace_empty_values_by_missing, _unicode(widget_sub.url))
        to.success_message = _replace(replace_empty_values_by_missing, _unicode(widget_sub.successMessage))
        to.caption = _replace(replace_empty_values_by_missing, _unicode(widget_sub.caption))
        return to


class OauthFormTO(FormTO):
    widget = typed_property('2', OauthTO, False)


class OauthFormMessageTO(FormMessageTO):
    form = typed_property('51', OauthFormTO, False)


class NewOauthFormRequestTO(object):
    form_message = typed_property('1', OauthFormMessageTO, False)


class NewOauthFormResponseTO(NewMessageResponseTO):
    pass


class PaymentMethodTO(PaymentMethod):
    pass


class PayTO(Pay):

    @classmethod
    def fromWidget(cls, model, form_result=None):
        to = cls()
        to.__dict__ = model.__dict__
        return to

    @classmethod
    def fromWidgetXmlSub(cls, widget_sub, replace_empty_values_by_missing=True):
        # type: (PayWidget, bool) -> PayTO
        to = cls()
        to.methods = []
        for m in widget_sub.get_method():
            method = PaymentMethodTO(
                provider_id=_replace(replace_empty_values_by_missing, _unicode(m.provider_id)),
                currency=_replace(replace_empty_values_by_missing, _unicode(m.currency)),
                amount=_replace(replace_empty_values_by_missing, m.amount),
                target=_replace(replace_empty_values_by_missing, m.target),
                precision=_replace(replace_empty_values_by_missing, m.precision),
                calculate_amount=_replace(replace_empty_values_by_missing, m.calculateAmount),
            )
            to.methods.append(method)
        to.memo = _replace(replace_empty_values_by_missing, _unicode(widget_sub.memo))
        to.target = _replace(replace_empty_values_by_missing, _unicode(widget_sub.target))
        to.auto_submit = _replace(replace_empty_values_by_missing, widget_sub.autoSubmit)
        to.test_mode = _replace(replace_empty_values_by_missing, widget_sub.testMode)
        to.embedded_app_id = _replace(replace_empty_values_by_missing, _unicode(widget_sub.embeddedAppId))
        if widget_sub.baseMethod:
            to.base_method = BasePaymentMethod(currency=widget_sub.baseMethod.currency,
                                               amount=widget_sub.baseMethod.amount,
                                               precision=widget_sub.baseMethod.precision)
        return to


class PayFormTO(FormTO):
    widget = typed_property('2', PayTO, False)


class PayFormMessageTO(FormMessageTO):
    form = typed_property('51', PayFormTO, False)


class NewPayFormRequestTO(object):
    form_message = typed_property('1', PayFormMessageTO, False)


class NewPayFormResponseTO(NewMessageResponseTO):
    pass


class UnicodeWidgetResultTO(UnicodeWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.value = wr.value
        return to


class UnicodeListWidgetResultTO(UnicodeListWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.values = wr.values
        return to


class LongWidgetResultTO(LongWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.value = wr.value
        return to


class LongListWidgetResultTO(LongListWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.values = wr.values
        return to


class FloatWidgetResultTO(FloatWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.value = wr.value
        return to


class FloatListWidgetResultTO(FloatListWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.values = wr.values
        return to


class LocationWidgetResultTO(LocationWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.horizontal_accuracy = wr.horizontal_accuracy
        to.vertical_accuracy = wr.vertical_accuracy
        to.latitude = wr.latitude
        to.longitude = wr.longitude
        to.altitude = wr.altitude
        to.timestamp = wr.timestamp
        return to


class MyDigiPassWidgetResultTO(MyDigiPassWidgetResult):

    def __init__(self, initialize=False):
        MyDigiPassWidgetResult.__init__(self)
        if initialize:
            complex_members, simple_members = get_members(MyDigiPassWidgetResultTO)
            for attr, _ in itertools.chain(complex_members, simple_members):
                setattr(self, attr, MISSING)

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.__dict__ = wr.__dict__
        return to


class OpenIdWidgetResultTO(OpenIdWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.__dict__ = wr.__dict__
        return to


class AdvancedOrderWidgetResultTO(AdvancedOrderWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.__dict__ = wr.__dict__
        return to


class SignWidgetResultTO(SignWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.__dict__ = wr.__dict__
        return to

class PayWidgetResultTO(PayWidgetResult):

    @classmethod
    def fromWidgetResult(cls, wr):
        to = cls()
        to.__dict__ = wr.__dict__
        return to


class SubmitFormRequestTO(object):
    message_key = unicode_property('1')
    parent_message_key = unicode_property('2')
    button_id = unicode_property('3')
    result = typed_property('4', WidgetResult, False)
    timestamp = long_property('5')


class SubmitFormResponseTO(AckMessageResponseTO):
    pass


class SubmitTextLineFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitTextLineFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitTextBlockFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitTextBlockFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitAutoCompleteFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitAutoCompleteFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitFriendSelectFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeListWidgetResultTO, False)


class SubmitFriendSelectFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitSingleSelectFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitSingleSelectFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitMultiSelectFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeListWidgetResultTO, False)


class SubmitMultiSelectFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitDateSelectFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', LongWidgetResultTO, False)


class SubmitDateSelectFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitSingleSliderFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', FloatWidgetResultTO, False)


class SubmitSingleSliderFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitRangeSliderFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', FloatListWidgetResultTO, False)


class SubmitRangeSliderFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitPhotoUploadFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitPhotoUploadFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitGPSLocationFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', LocationWidgetResultTO, False)


class SubmitGPSLocationFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitMyDigiPassFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', MyDigiPassWidgetResultTO, False)


class SubmitMyDigiPassFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitOpenIdFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', OpenIdWidgetResultTO)


class SubmitOpenIdFormResponseTO(SubmitFormRequestTO):
    pass


class SubmitAdvancedOrderFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', AdvancedOrderWidgetResultTO, False)


class SubmitAdvancedOrderFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitSignFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', SignWidgetResultTO, False)


class SubmitSignFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitOauthFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', UnicodeWidgetResultTO, False)


class SubmitOauthFormResponseTO(SubmitFormResponseTO):
    pass


class SubmitPayFormRequestTO(SubmitFormRequestTO):
    result = typed_property('4', PayWidgetResultTO, False)


class SubmitPayFormResponseTO(SubmitFormResponseTO):
    pass


class UpdateFormRequestTO(object):
    parent_message_key = unicode_property('0')
    message_key = unicode_property('1')
    button_id = unicode_property('2')
    received_timestamp = long_property('3')
    acked_timestamp = long_property('4')
    result = typed_property('5', WidgetResult, False)
    status = long_property('6')

    @staticmethod
    def fromMessageAndMember(fm, user):
        ms = fm.memberStatusses[fm.members.index(user)]
        req = WIDGET_MAPPING[fm.form.type].form_updated_req_to_type()
        req.message_key = fm.mkey
        req.parent_message_key = fm.pkey
        req.button_id = None if ms.button_index < 0 else fm.buttons[ms.button_index].id
        req.acked_timestamp = ms.acked_timestamp
        req.received_timestamp = ms.received_timestamp
        if ms.form_result and ms.form_result.result:
            req.result = WIDGET_RESULT_TO_MAPPING[ms.form_result.type].fromWidgetResult(ms.form_result.result)
        else:
            req.result = None
        req.status = ms.status
        return req


class UpdateFormResponseTO(object):
    pass


class UpdateTextLineFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdateTextLineFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateTextBlockFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdateTextBlockFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateAutoCompleteFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdateAutoCompleteFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateFriendSelectFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeListWidgetResultTO, False)


class UpdateFriendSelectFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateSingleSelectFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdateSingleSelectFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateMultiSelectFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeListWidgetResultTO, False)


class UpdateMultiSelectFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateDateSelectFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', LongWidgetResultTO, False)


class UpdateDateSelectFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateSingleSliderFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', FloatWidgetResultTO, False)


class UpdateSingleSliderFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateRangeSliderFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', FloatListWidgetResultTO, False)


class UpdateRangeSliderFormResponseTO(UpdateFormResponseTO):
    pass


class UpdatePhotoUploadFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdatePhotoUploadFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateGPSLocationFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', LocationWidgetResultTO, False)


class UpdateGPSLocationFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateMyDigiPassFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', MyDigiPassWidgetResultTO, False)


class UpdateMyDigiPassFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateOpenIdFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateOpenIdFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', OpenIdWidgetResultTO, False)


class UpdateAdvancedOrderFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', AdvancedOrderWidgetResultTO, False)


class UpdateAdvancedOrderFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateSignFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', SignWidgetResultTO, False)


class UpdateSignFormResponseTO(UpdateFormResponseTO):
    pass


class UpdateOauthFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', UnicodeWidgetResultTO, False)


class UpdateOauthFormResponseTO(UpdateFormResponseTO):
    pass


class UpdatePayFormRequestTO(UpdateFormRequestTO):
    result = typed_property('5', PayWidgetResultTO, False)


class UpdatePayFormResponseTO(UpdateFormResponseTO):
    pass
