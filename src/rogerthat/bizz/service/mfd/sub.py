#!/usr/bin/env python
# @@xxx_skip_license@@
# @PydevCodeAnalysisIgnore

#
# Generated Tue Nov  6 11:26:05 2018 by generateDS.py version 2.29.24.
# Python 3.7.0 (default, Jul 23 2018, 20:22:55)  [Clang 9.1.0 (clang-902.0.39.2)]
#
# Command line options:
#   ('-f', '')
#   ('--no-questions', '')
#   ('--external-encoding', 'utf-8')
#   ('-o', 'gen.py')
#   ('-s', 'sub.py')
#
# Command line arguments:
#   ../../../service/api/MessageFlow.1.xsd
#
# Command line:
#   /usr/local/bin/generateDS -f --no-questions --external-encoding="utf-8" -o "gen.py" -s "sub.py" ../../../service/api/MessageFlow.1.xsd
#
# Current working directory (os.getcwd()):
#   mfd
#

import sys
from lxml import etree as etree_

from rogerthat.bizz.service.mfd import gen as supermod

def parsexml_(infile, parser=None, **kwargs):
    if parser is None:
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        parser = etree_.ETCompatXMLParser()
    doc = etree_.parse(infile, parser=parser, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'utf-8'

#
# Data representation classes
#


class AttachmentSub(supermod.Attachment):
    def __init__(self, name=None, url=None, contentType=None, size=None):
        super(AttachmentSub, self).__init__(name, url, contentType, size, )
supermod.Attachment.subclass = AttachmentSub
# end class AttachmentSub


class FlowElementSub(supermod.FlowElement):
    def __init__(self, id=None, extensiontype_=None):
        super(FlowElementSub, self).__init__(id, extensiontype_, )
supermod.FlowElement.subclass = FlowElementSub
# end class FlowElementSub


class AnswerSub(supermod.Answer):
    def __init__(self, caption=None, action=None, id=None, reference=None, color=None):
        super(AnswerSub, self).__init__(caption, action, id, reference, color, )
supermod.Answer.subclass = AnswerSub
# end class AnswerSub


class MessageSub(supermod.Message):
    def __init__(self, id=None, allowDismiss=None, dismissReference=None, brandingKey=None, autoLock=None, vibrate=None, alertType=None, alertIntervalType=None, content=None, answer=None, attachment=None):
        super(MessageSub, self).__init__(id, allowDismiss, dismissReference, brandingKey, autoLock, vibrate, alertType, alertIntervalType, content, answer, attachment, )
supermod.Message.subclass = MessageSub
# end class MessageSub


class ResultsFlushSub(supermod.ResultsFlush):
    def __init__(self, id=None, reference=None):
        super(ResultsFlushSub, self).__init__(id, reference, )
supermod.ResultsFlush.subclass = ResultsFlushSub
# end class ResultsFlushSub


class ResultsEmailSub(supermod.ResultsEmail):
    def __init__(self, id=None, reference=None, emailAdmins=None, email=None):
        super(ResultsEmailSub, self).__init__(id, reference, emailAdmins, email, )
supermod.ResultsEmail.subclass = ResultsEmailSub
# end class ResultsEmailSub


class FlowCodeSub(supermod.FlowCode):
    def __init__(self, id=None, exceptionReference=None, outlet=None, javascriptCode=None):
        super(FlowCodeSub, self).__init__(id, exceptionReference, outlet, javascriptCode, )
supermod.FlowCode.subclass = FlowCodeSub
# end class FlowCodeSub


class WidgetSub(supermod.Widget):
    def __init__(self, extensiontype_=None):
        super(WidgetSub, self).__init__(extensiontype_, )
supermod.Widget.subclass = WidgetSub
# end class WidgetSub


class BaseSliderWidgetSub(supermod.BaseSliderWidget):
    def __init__(self, min=None, max=None, step=None, precision=None, unit=None, extensiontype_=None):
        super(BaseSliderWidgetSub, self).__init__(min, max, step, precision, unit, extensiontype_, )
supermod.BaseSliderWidget.subclass = BaseSliderWidgetSub
# end class BaseSliderWidgetSub


class SliderWidgetSub(supermod.SliderWidget):
    def __init__(self, min=None, max=None, step=None, precision=None, unit=None, value=None):
        super(SliderWidgetSub, self).__init__(min, max, step, precision, unit, value, )
supermod.SliderWidget.subclass = SliderWidgetSub
# end class SliderWidgetSub


class RangeSliderWidgetSub(supermod.RangeSliderWidget):
    def __init__(self, min=None, max=None, step=None, precision=None, unit=None, lowValue=None, highValue=None):
        super(RangeSliderWidgetSub, self).__init__(min, max, step, precision, unit, lowValue, highValue, )
supermod.RangeSliderWidget.subclass = RangeSliderWidgetSub
# end class RangeSliderWidgetSub


class PhotoUploadWidgetSub(supermod.PhotoUploadWidget):
    def __init__(self, quality=None, gallery=None, camera=None, ratio=None):
        super(PhotoUploadWidgetSub, self).__init__(quality, gallery, camera, ratio, )
supermod.PhotoUploadWidget.subclass = PhotoUploadWidgetSub
# end class PhotoUploadWidgetSub


class GPSLocationWidgetSub(supermod.GPSLocationWidget):
    def __init__(self, gps=None):
        super(GPSLocationWidgetSub, self).__init__(gps, )
supermod.GPSLocationWidget.subclass = GPSLocationWidgetSub
# end class GPSLocationWidgetSub


class TextWidgetSub(supermod.TextWidget):
    def __init__(self, maxChars=None, placeholder=None, value=None, keyboardType=None, extensiontype_=None):
        super(TextWidgetSub, self).__init__(maxChars, placeholder, value, keyboardType, extensiontype_, )
supermod.TextWidget.subclass = TextWidgetSub
# end class TextWidgetSub


class TextLineWidgetSub(supermod.TextLineWidget):
    def __init__(self, maxChars=None, placeholder=None, value=None, keyboardType=None):
        super(TextLineWidgetSub, self).__init__(maxChars, placeholder, value, keyboardType, )
supermod.TextLineWidget.subclass = TextLineWidgetSub
# end class TextLineWidgetSub


class TextBlockWidgetSub(supermod.TextBlockWidget):
    def __init__(self, maxChars=None, placeholder=None, value=None, keyboardType=None):
        super(TextBlockWidgetSub, self).__init__(maxChars, placeholder, value, keyboardType, )
supermod.TextBlockWidget.subclass = TextBlockWidgetSub
# end class TextBlockWidgetSub


class ValueSub(supermod.Value):
    def __init__(self, value=None, extensiontype_=None):
        super(ValueSub, self).__init__(value, extensiontype_, )
supermod.Value.subclass = ValueSub
# end class ValueSub


class FloatValueSub(supermod.FloatValue):
    def __init__(self, value=None):
        super(FloatValueSub, self).__init__(value, )
supermod.FloatValue.subclass = FloatValueSub
# end class FloatValueSub


class AdvancedOrderCategorySub(supermod.AdvancedOrderCategory):
    def __init__(self, id=None, name=None, item=None):
        super(AdvancedOrderCategorySub, self).__init__(id, name, item, )
supermod.AdvancedOrderCategory.subclass = AdvancedOrderCategorySub
# end class AdvancedOrderCategorySub


class AdvancedOrderItemSub(supermod.AdvancedOrderItem):
    def __init__(self, id=None, value=None, unit=None, unitPrice=None, hasPrice=True, step=None, stepUnit=None, stepUnitConversion=None, imageUrl=None, name=None, description=None):
        super(AdvancedOrderItemSub, self).__init__(id, value, unit, unitPrice, hasPrice, step, stepUnit, stepUnitConversion, imageUrl, name, description, )
supermod.AdvancedOrderItem.subclass = AdvancedOrderItemSub
# end class AdvancedOrderItemSub


class BasePaymentMethodSub(supermod.BasePaymentMethod):
    def __init__(self, id=None, currency=None, amount=None, precision=None, extensiontype_=None):
        super(BasePaymentMethodSub, self).__init__(id, currency, amount, precision, extensiontype_, )
supermod.BasePaymentMethod.subclass = BasePaymentMethodSub
# end class BasePaymentMethodSub


class PaymentMethodSub(supermod.PaymentMethod):
    def __init__(self, id=None, currency=None, amount=None, precision=None, provider_id=None, calculateAmount=False, target=None):
        super(PaymentMethodSub, self).__init__(id, currency, amount, precision, provider_id, calculateAmount, target, )
supermod.PaymentMethod.subclass = PaymentMethodSub
# end class PaymentMethodSub


class TextAutocompleteWidgetSub(supermod.TextAutocompleteWidget):
    def __init__(self, maxChars=None, placeholder=None, value=None, keyboardType=None, suggestion=None):
        super(TextAutocompleteWidgetSub, self).__init__(maxChars, placeholder, value, keyboardType, suggestion, )
supermod.TextAutocompleteWidget.subclass = TextAutocompleteWidgetSub
# end class TextAutocompleteWidgetSub


class ChoiceSub(supermod.Choice):
    def __init__(self, value=None, label=None):
        super(ChoiceSub, self).__init__(value, label, )
supermod.Choice.subclass = ChoiceSub
# end class ChoiceSub


class SelectWidgetSub(supermod.SelectWidget):
    def __init__(self, choice=None, extensiontype_=None):
        super(SelectWidgetSub, self).__init__(choice, extensiontype_, )
supermod.SelectWidget.subclass = SelectWidgetSub
# end class SelectWidgetSub


class SelectSingleWidgetSub(supermod.SelectSingleWidget):
    def __init__(self, choice=None, value=None):
        super(SelectSingleWidgetSub, self).__init__(choice, value, )
supermod.SelectSingleWidget.subclass = SelectSingleWidgetSub
# end class SelectSingleWidgetSub


class SelectMultiWidgetSub(supermod.SelectMultiWidget):
    def __init__(self, choice=None, value=None):
        super(SelectMultiWidgetSub, self).__init__(choice, value, )
supermod.SelectMultiWidget.subclass = SelectMultiWidgetSub
# end class SelectMultiWidgetSub


class SelectDateWidgetSub(supermod.SelectDateWidget):
    def __init__(self, minDate=None, maxDate=None, date=None, minuteInterval=None, mode=None, unit=None):
        super(SelectDateWidgetSub, self).__init__(minDate, maxDate, date, minuteInterval, mode, unit, )
supermod.SelectDateWidget.subclass = SelectDateWidgetSub
# end class SelectDateWidgetSub


class SelectFriendWidgetSub(supermod.SelectFriendWidget):
    def __init__(self, selectionRequired=None, multiSelect=None):
        super(SelectFriendWidgetSub, self).__init__(selectionRequired, multiSelect, )
supermod.SelectFriendWidget.subclass = SelectFriendWidgetSub
# end class SelectFriendWidgetSub


class MyDigiPassWidgetSub(supermod.MyDigiPassWidget):
    def __init__(self, scope=None):
        super(MyDigiPassWidgetSub, self).__init__(scope, )
supermod.MyDigiPassWidget.subclass = MyDigiPassWidgetSub
# end class MyDigiPassWidgetSub


class OpenIdWidgetSub(supermod.OpenIdWidget):
    def __init__(self, provider=None, scope=None):
        super(OpenIdWidgetSub, self).__init__(provider, scope, )
supermod.OpenIdWidget.subclass = OpenIdWidgetSub
# end class OpenIdWidgetSub


class AdvancedOrderWidgetSub(supermod.AdvancedOrderWidget):
    def __init__(self, currency=None, leapTime=None, category=None):
        super(AdvancedOrderWidgetSub, self).__init__(currency, leapTime, category, )
supermod.AdvancedOrderWidget.subclass = AdvancedOrderWidgetSub
# end class AdvancedOrderWidgetSub


class SignWidgetSub(supermod.SignWidget):
    def __init__(self, caption=None, algorithm=None, keyName=None, index=None, payload=None):
        super(SignWidgetSub, self).__init__(caption, algorithm, keyName, index, payload, )
supermod.SignWidget.subclass = SignWidgetSub
# end class SignWidgetSub


class OauthWidgetSub(supermod.OauthWidget):
    def __init__(self, url=None, caption=None, successMessage=None):
        super(OauthWidgetSub, self).__init__(url, caption, successMessage, )
supermod.OauthWidget.subclass = OauthWidgetSub
# end class OauthWidgetSub


class PayWidgetSub(supermod.PayWidget):
    def __init__(self, memo=None, target=None, autoSubmit=True, testMode=False, embeddedAppId=None, method=None, baseMethod=None):
        super(PayWidgetSub, self).__init__(memo, target, autoSubmit, testMode, embeddedAppId, method, baseMethod, )
supermod.PayWidget.subclass = PayWidgetSub
# end class PayWidgetSub


class FormSub(supermod.Form):
    def __init__(self, positiveButtonCaption=None, positiveButtonConfirmation=None, negativeButtonCaption=None, negativeButtonConfirmation=None, widget=None, javascriptValidation=None):
        super(FormSub, self).__init__(positiveButtonCaption, positiveButtonConfirmation, negativeButtonCaption, negativeButtonConfirmation, widget, javascriptValidation, )
supermod.Form.subclass = FormSub
# end class FormSub


class FormMessageSub(supermod.FormMessage):
    def __init__(self, id=None, member=None, brandingKey=None, autoLock=None, vibrate=None, alertType=None, alertIntervalType=None, positiveReference=None, negativeReference=None, content=None, form=None, attachment=None):
        super(FormMessageSub, self).__init__(id, member, brandingKey, autoLock, vibrate, alertType, alertIntervalType, positiveReference, negativeReference, content, form, attachment, )
supermod.FormMessage.subclass = FormMessageSub
# end class FormMessageSub


class OutletSub(supermod.Outlet):
    def __init__(self, value=None, name=None, reference=None):
        super(OutletSub, self).__init__(value, name, reference, )
supermod.Outlet.subclass = OutletSub
# end class OutletSub


class EndSub(supermod.End):
    def __init__(self, id=None, waitForFollowUpMessage=False):
        super(EndSub, self).__init__(id, waitForFollowUpMessage, )
supermod.End.subclass = EndSub
# end class EndSub


class MessageFlowDefinitionSub(supermod.MessageFlowDefinition):
    def __init__(self, name=None, startReference=None, language=None, end=None, message=None, formMessage=None, resultsFlush=None, resultsEmail=None, flowCode=None):
        super(MessageFlowDefinitionSub, self).__init__(name, startReference, language, end, message, formMessage, resultsFlush, resultsEmail, flowCode, )
supermod.MessageFlowDefinition.subclass = MessageFlowDefinitionSub
# end class MessageFlowDefinitionSub


class MessageFlowDefinitionSetSub(supermod.MessageFlowDefinitionSet):
    def __init__(self, definition=None):
        super(MessageFlowDefinitionSetSub, self).__init__(definition, )
supermod.MessageFlowDefinitionSet.subclass = MessageFlowDefinitionSetSub
# end class MessageFlowDefinitionSetSub


class StepSub(supermod.Step):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, extensiontype_=None):
        super(StepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, extensiontype_, )
supermod.Step.subclass = StepSub
# end class StepSub


class BaseMessageStepSub(supermod.BaseMessageStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, extensiontype_=None):
        super(BaseMessageStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, extensiontype_, )
supermod.BaseMessageStep.subclass = BaseMessageStepSub
# end class BaseMessageStepSub


class MessageStepSub(supermod.MessageStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, answer=None):
        super(MessageStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, answer, )
supermod.MessageStep.subclass = MessageStepSub
# end class MessageStepSub


class WidgetStepSub(supermod.WidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, extensiontype_=None):
        super(WidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, extensiontype_, )
supermod.WidgetStep.subclass = WidgetStepSub
# end class WidgetStepSub


class TextWidgetStepSub(supermod.TextWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None, extensiontype_=None):
        super(TextWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, extensiontype_, )
supermod.TextWidgetStep.subclass = TextWidgetStepSub
# end class TextWidgetStepSub


class TextLineWidgetStepSub(supermod.TextLineWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(TextLineWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.TextLineWidgetStep.subclass = TextLineWidgetStepSub
# end class TextLineWidgetStepSub


class TextBlockWidgetStepSub(supermod.TextBlockWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(TextBlockWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.TextBlockWidgetStep.subclass = TextBlockWidgetStepSub
# end class TextBlockWidgetStepSub


class TextAutoCompleteWidgetStepSub(supermod.TextAutoCompleteWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(TextAutoCompleteWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.TextAutoCompleteWidgetStep.subclass = TextAutoCompleteWidgetStepSub
# end class TextAutoCompleteWidgetStepSub


class SliderWidgetStepSub(supermod.SliderWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(SliderWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.SliderWidgetStep.subclass = SliderWidgetStepSub
# end class SliderWidgetStepSub


class RangeSliderWidgetStepSub(supermod.RangeSliderWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(RangeSliderWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.RangeSliderWidgetStep.subclass = RangeSliderWidgetStepSub
# end class RangeSliderWidgetStepSub


class PhotoUploadWidgetStepSub(supermod.PhotoUploadWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(PhotoUploadWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.PhotoUploadWidgetStep.subclass = PhotoUploadWidgetStepSub
# end class PhotoUploadWidgetStepSub


class GPSLocationWidgetStepSub(supermod.GPSLocationWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, horizontalAccuracy=None, verticalAccuracy=None, latitude=None, longitude=None, altitude=None, timestamp=None):
        super(GPSLocationWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, horizontalAccuracy, verticalAccuracy, latitude, longitude, altitude, timestamp, )
supermod.GPSLocationWidgetStep.subclass = GPSLocationWidgetStepSub
# end class GPSLocationWidgetStepSub


class MyDigiPassEidProfileSub(supermod.MyDigiPassEidProfile):
    def __init__(self, firstName=None, firstName3=None, lastName=None, gender=None, nationality=None, dateOfBirth=None, locationOfBirth=None, nobleCondition=None, issuingMunicipality=None, cardNumber=None, chipNumber=None, validityBeginsAt=None, validityEndsAt=None, createdAt=None):
        super(MyDigiPassEidProfileSub, self).__init__(firstName, firstName3, lastName, gender, nationality, dateOfBirth, locationOfBirth, nobleCondition, issuingMunicipality, cardNumber, chipNumber, validityBeginsAt, validityEndsAt, createdAt, )
supermod.MyDigiPassEidProfile.subclass = MyDigiPassEidProfileSub
# end class MyDigiPassEidProfileSub


class MyDigiPassEidAddressSub(supermod.MyDigiPassEidAddress):
    def __init__(self, streetAndNumber=None, zipCode=None, municipality=None):
        super(MyDigiPassEidAddressSub, self).__init__(streetAndNumber, zipCode, municipality, )
supermod.MyDigiPassEidAddress.subclass = MyDigiPassEidAddressSub
# end class MyDigiPassEidAddressSub


class MyDigiPassProfileSub(supermod.MyDigiPassProfile):
    def __init__(self, updatedAt=None, firstName=None, lastName=None, bornOn=None, preferredLocale=None, uuid=None):
        super(MyDigiPassProfileSub, self).__init__(updatedAt, firstName, lastName, bornOn, preferredLocale, uuid, )
supermod.MyDigiPassProfile.subclass = MyDigiPassProfileSub
# end class MyDigiPassProfileSub


class MyDigiPassAddressSub(supermod.MyDigiPassAddress):
    def __init__(self, address1=None, address2=None, city=None, zip=None, country=None, state=None):
        super(MyDigiPassAddressSub, self).__init__(address1, address2, city, zip, country, state, )
supermod.MyDigiPassAddress.subclass = MyDigiPassAddressSub
# end class MyDigiPassAddressSub


class MyDigiPassWidgetStepSub(supermod.MyDigiPassWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, eidPhoto=None, email=None, phone=None, eidProfile=None, eidAddress=None, profile=None, address=None):
        super(MyDigiPassWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, eidPhoto, email, phone, eidProfile, eidAddress, profile, address, )
supermod.MyDigiPassWidgetStep.subclass = MyDigiPassWidgetStepSub
# end class MyDigiPassWidgetStepSub


class SelectSingleWidgetStepSub(supermod.SelectSingleWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, value=None):
        super(SelectSingleWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, value, )
supermod.SelectSingleWidgetStep.subclass = SelectSingleWidgetStepSub
# end class SelectSingleWidgetStepSub


class SelectMultiWidgetStepSub(supermod.SelectMultiWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, selection=None):
        super(SelectMultiWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, selection, )
supermod.SelectMultiWidgetStep.subclass = SelectMultiWidgetStepSub
# end class SelectMultiWidgetStepSub


class SelectDateWidgetStepSub(supermod.SelectDateWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, date=None):
        super(SelectDateWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, date, )
supermod.SelectDateWidgetStep.subclass = SelectDateWidgetStepSub
# end class SelectDateWidgetStepSub


class SelectFriendWidgetStepSub(supermod.SelectFriendWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, selection=None):
        super(SelectFriendWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, selection, )
supermod.SelectFriendWidgetStep.subclass = SelectFriendWidgetStepSub
# end class SelectFriendWidgetStepSub


class AdvancedOrderWidgetStepSub(supermod.AdvancedOrderWidgetStep):
    def __init__(self, id=None, creationTimestamp=None, definition=None, previousStep=None, nextStep=None, message=None, button=None, receivedTimestamp=None, acknowledgedTimestamp=None, displayValue=None, formButton=None, currency=None, category=None):
        super(AdvancedOrderWidgetStepSub, self).__init__(id, creationTimestamp, definition, previousStep, nextStep, message, button, receivedTimestamp, acknowledgedTimestamp, displayValue, formButton, currency, category, )
supermod.AdvancedOrderWidgetStep.subclass = AdvancedOrderWidgetStepSub
# end class AdvancedOrderWidgetStepSub


class MemberRunSub(supermod.MemberRun):
    def __init__(self, email=None, name=None, status=None, endReference=None, language=None, appId=None, avatarUrl=None, userData=None, step=None):
        super(MemberRunSub, self).__init__(email, name, status, endReference, language, appId, avatarUrl, userData, step, )
supermod.MemberRun.subclass = MemberRunSub
# end class MemberRunSub


class MessageFlowRunSub(supermod.MessageFlowRun):
    def __init__(self, launchTimestamp=None, serviceName=None, serviceDisplayEmail=None, serviceEmail=None, serviceData=None, definition=None, memberRun=None, flowParams=None):
        super(MessageFlowRunSub, self).__init__(launchTimestamp, serviceName, serviceDisplayEmail, serviceEmail, serviceData, definition, memberRun, flowParams, )
supermod.MessageFlowRun.subclass = MessageFlowRunSub
# end class MessageFlowRunSub


class contentTypeSub(supermod.contentType):
    def __init__(self, valueOf_=None):
        super(contentTypeSub, self).__init__(valueOf_, )
supermod.contentType.subclass = contentTypeSub
# end class contentTypeSub


class javascriptCodeTypeSub(supermod.javascriptCodeType):
    def __init__(self, valueOf_=None):
        super(javascriptCodeTypeSub, self).__init__(valueOf_, )
supermod.javascriptCodeType.subclass = javascriptCodeTypeSub
# end class javascriptCodeTypeSub


class contentType1Sub(supermod.contentType1):
    def __init__(self, valueOf_=None):
        super(contentType1Sub, self).__init__(valueOf_, )
supermod.contentType1.subclass = contentType1Sub
# end class contentType1Sub


def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    rootClass = supermod.GDSClassesMapping.get(tag)
    if rootClass is None and hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'Attachment'
        rootClass = supermod.Attachment
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='',
            pretty_print=True)
    return rootObj


def parseEtree(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'Attachment'
        rootClass = supermod.Attachment
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    mapping = {}
    rootElement = rootObj.to_etree(None, name_=rootTag, mapping_=mapping)
    reverse_mapping = rootObj.gds_reverse_node_mapping(mapping)
    if not silence:
        content = etree_.tostring(
            rootElement, pretty_print=True,
            xml_declaration=True, encoding="utf-8")
        sys.stdout.write(content)
        sys.stdout.write('\n')
    return rootObj, rootElement, mapping, reverse_mapping


def parseString(inString, silence=False):
    if sys.version_info.major == 2:
        from StringIO import StringIO
    else:
        from io import BytesIO as StringIO
    parser = None
    doc = parsexml_(StringIO(inString), parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'Attachment'
        rootClass = supermod.Attachment
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='')
    return rootObj


def parseLiteral(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'Attachment'
        rootClass = supermod.Attachment
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('#from ??? import *\n\n')
        sys.stdout.write('import ??? as model_\n\n')
        sys.stdout.write('rootObj = model_.rootClass(\n')
        rootObj.exportLiteral(sys.stdout, 0, name_=rootTag)
        sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""


def usage():
    print(USAGE_TEXT)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()