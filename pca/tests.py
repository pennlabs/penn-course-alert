from django.test import TestCase
from unittest.mock import Mock, patch

from pca import tasks
from pca.models import *


def contains_all(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


@patch('pca.models.Text.send_alert')
@patch('pca.models.Email.send_alert')
class SendAlertTestCase(TestCase):
    def setUp(self):
        course, section = get_course_and_section('CIS-160-001', '2019A')
        self.r = Registration(email='yo@example.com',
                              phone='+15555555555',
                              section=section)

        self.r.save()

    def test_send_alert(self, mock_email, mock_text):
        self.assertFalse(Registration.objects.get(id=self.r.id).notification_sent)
        tasks.send_alert(self.r.id)
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)
        self.assertTrue(Registration.objects.get(id=self.r.id).notification_sent)

    def test_dont_resend_alert(self, mock_email, mock_text):
        self.r.notification_sent = True
        self.r.save()
        tasks.send_alert(self.r.id)
        self.assertFalse(mock_email.called)
        self.assertFalse(mock_text.called)

    def test_resend_alert_forced(self, mock_email, mock_text):
        self.r.notification_sent = True
        self.r.save()
        self.r.alert(True)
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)


@patch('pca.tasks.api.get_course')
class SendAlertsForSectionTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-160-001', '2019A')
        with open('pca/mock_registrar_response.json', 'r') as f:
            self.response = json.load(f)

    def assert_should_send(self, mock_get, was_open, now_open, should_send):
        self.section.is_open = was_open
        self.section.save()

        self.response['course_status'] = 'O' if now_open else 'C'
        mock_get.return_value = self.response

        result = tasks.should_send_alert(self.section.normalized, self.course.semester)
        self.assertTrue(mock_get.called)
        self.assertEquals(result, should_send)

    def test_open_then_closed(self, mock_get):
        self.assert_should_send(mock_get, True, False, False)

    def test_closed_then_closed(self, mock_get):
        self.assert_should_send(mock_get, False, False, False)

    def test_closed_then_open(self, mock_get):
        self.assert_should_send(mock_get, False, True, True)

    def test_open_then_open(self, mock_get):
        # was_open shouldn't have an effect on sending without perpetual notifications
        self.assert_should_send(mock_get, True, True, True)


class CollectRegistrationTestCase(TestCase):
    def setUp(self):
        self.sections = []
        self.sections.append(get_course_and_section('CIS-160-001', '2019A')[1])
        self.sections.append(get_course_and_section('CIS-160-002', '2019A')[1])
        self.sections.append(get_course_and_section('CIS-160-001', '2018A')[1])
        self.sections.append(get_course_and_section('CIS-120-001', '2019A')[1])

    def test_no_registrations(self):
        result = tasks.collect_registrations('2019A')
        self.assertEqual(0, len(result))

    def test_one_registration(self):
        r = Registration(email='e@example.com', section=self.sections[0])
        r.save()
        result = tasks.collect_registrations('2019A')
        self.assertEqual(1, len(result))
        self.assertTrue(contains_all(result[self.sections[0].normalized], [r.id]))

    def test_two_classes(self):
        r1 = Registration(email='e@example.com', section=self.sections[0])
        r2 = Registration(email='e@example.com', section=self.sections[3])
        r1.save()
        r2.save()
        result = tasks.collect_registrations('2019A')
        self.assertDictEqual(result, {
            self.sections[0].normalized: [r1.id],
            self.sections[3].normalized: [r2.id]
        })

    def test_only_current_semester(self):
        r1 = Registration(email='e@example.com', section=self.sections[0])
        r2 = Registration(email='e@example.com', section=self.sections[2])
        r1.save()
        r2.save()
        result = tasks.collect_registrations('2019A')
        self.assertDictEqual(result, {
            self.sections[0].normalized: [r1.id]
        })

    def test_two_sections(self):
        r1 = Registration(email='e@example.com', section=self.sections[0])
        r2 = Registration(email='e@example.com', section=self.sections[1])
        r1.save()
        r2.save()
        result = tasks.collect_registrations('2019A')
        self.assertDictEqual(result, {
            self.sections[0].normalized: [r1.id],
            self.sections[1].normalized: [r2.id]
        })

    def test_two_registrations_same_section(self):
        r1 = Registration(email='e@example.com', section=self.sections[0])
        r2 = Registration(email='v@example.com', section=self.sections[0])
        r1.save()
        r2.save()
        result = tasks.collect_registrations('2019A')
        self.assertEqual(1, len(result))
        self.assertTrue(contains_all([r1.id, r2.id], result[self.sections[0].normalized]))

    def test_only_unused_registrations(self):
        r1 = Registration(email='e@example.com', section=self.sections[0])
        r2 = Registration(email='v@example.com', section=self.sections[0], notification_sent=True)
        r1.save()
        r2.save()
        result = tasks.collect_registrations('2019A')
        self.assertEqual(1, len(result))
        self.assertTrue(contains_all([r1.id], result[self.sections[0].normalized]))


class RegisterTestCase(TestCase):
    def setUp(self):
        self.sections = []
        self.sections.append(get_course_and_section('CIS-160-001', '2019A')[1])
        self.sections.append(get_course_and_section('CIS-160-002', '2019A')[1])
        self.sections.append(get_course_and_section('CIS-120-001', '2019A')[1])

    def test_successful_registration(self):
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual(self.sections[0].normalized, r.section.normalized)
        self.assertEqual('e@example.com', r.email)
        self.assertEqual('+15555555555', r.phone)
        self.assertFalse(r.notification_sent)

    def test_duplicate_registration(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.OPEN_REG_EXISTS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_reregister(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0], notification_sent=True)
        r1.save()
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffsections(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[1].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffcourse(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[2].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_justemail(self):
        res = register_for_course(self.sections[0].normalized, 'e@example.com', None)
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_justphone(self):
        res = register_for_course(self.sections[0].normalized, None, '5555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_nocontact(self):
        res = register_for_course(self.sections[0].normalized, None, None)
        self.assertEqual(RegStatus.NO_CONTACT_INFO, res)
        self.assertEqual(0, len(Registration.objects.all()))


class ResubscribeTestCase(TestCase):
    def setUp(self):
        _, self.section = get_course_and_section('CIS-160-001', '2019A')
        self.base_reg = Registration(email='e@example.com', phone='+15555555555', section=self.section)
        self.base_reg.save()

    def test_resubscribe(self):
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg = self.base_reg.resubscribe()
        self.assertNotEqual(reg, self.base_reg)
        self.assertEqual(self.base_reg, reg.resubscribed_from)

    def test_try_resubscribe_noalert(self):
        reg = self.base_reg.resubscribe()
        self.assertEqual(reg, self.base_reg)
        self.assertIsNone(reg.resubscribed_from)

    def test_resubscribe_oldlink(self):
        """following the resubscribe chain from an old link"""
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg1 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=self.base_reg,
                            notification_sent=True)
        reg1.save()
        reg2 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg1,
                            notification_sent=True)
        reg2.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result.resubscribed_from, reg2)

    def test_resubscribe_oldlink_noalert(self):
        """testing idempotence on old links"""
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg1 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=self.base_reg,
                            notification_sent=True)
        reg1.save()
        reg2 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg1,
                            notification_sent=True)
        reg2.save()
        reg3 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg2,
                            notification_sent=False)
        reg3.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result, reg3)


