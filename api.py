__author__ = 'Hung'

import requests
import json
from parser import Parser
from mailer import Mailer
from datetime import datetime, timedelta
import time
import copy


class API:
    @staticmethod
    def now():
        return '[' + time.strftime("%d/%m/%Y %H:%M:%S") + '] '

    # static strings
    @staticmethod
    def message(key):

        messages = {
            'launching': 'Welcome to use USport',
            'try_get_session': 'trying to get session, %d times',
            'fail_get_session': 'fail to get session',
            'display_session': 'session id: %s',
            'give_up': 'LET\'S GIVE UP :-(',
            'try_log_in': 'trying to log in as %s',
            'fail_log_in': 'fail to log in',
            'try_get_dates': 'trying to get available dates',
            'date_not_avail': '%s is not available for booking',
            'try_get_avail': 'trying to get availability on %s, %s, %d times',
            'no_courts_at_all': 'it seems no available on %s for %s at all',
            'try_time': 'see whether there are time %s matches',
            'try_court': 'see whether there are preferred court %s matches',
            'try_other_court': 'see whether other un preferred courts available',
            'fail_book': 'fail to make a booking',
            'try_book': 'trying to book %s at %s',
            'success': 'SUCCESS'
        }
        return API.now() + messages[key]

    # configs
    eid = None
    sid = None
    password = None
    user_type = None
    choice = None
    dateselect = None
    timeselect = []
    courtselect = []
    user_agent = None

    # email
    email = None
    success = 'FAIL'
    subject = 'USport Robot Result: %s'
    sender = 'robot@xinhong.me'
    mail_message = '''<div>Hi %s,</div><div>Here is the log of robot:</div><div><br></div><div><small>%s</small></div><div><br></div><div>Yours,</div><div>USport Robot&nbsp;</div><div>%s</div>'''
    reply = 'i@xinhong.me'

    # temp variables when booking
    booking_referer = None
    booking_parameters = None

    # vars
    cookies = dict()
    session_id = ''
    utility = None

    def __init__(self, user_config_json, target_config_json, sys_config_json):
        # read configs
        user_config = json.loads(user_config_json)
        target_config = json.loads(target_config_json)
        # set EID & SID & Password
        self.eid = str(user_config['eid'])
        self.password = str(user_config['password'])
        if 'email' in user_config:
            self.email = str(user_config['email'])
        self.choice = str(target_config['choice'])
        self.dateselect = str(target_config['date'])
        if self.dateselect.startswith('next '):
            # x in next week
            which_day = int(self.dateselect[-1:])
            n_w = timedelta(6 + which_day - datetime.today().weekday()) \
                + datetime.today()
            self.dateselect = n_w.strftime('%Y%m%d')
        if self.dateselect.startswith('coming '):
            # exclude today, next coming x
            which_day = int(self.dateselect[-1:])
            n_w = timedelta(which_day - 1 - datetime.today().weekday()) \
                + datetime.today()
            if datetime.today().weekday() + 1 >= which_day:
                n_w = timedelta(6 + which_day - datetime.today().weekday()) \
                    + datetime.today()
            self.dateselect = n_w.strftime('%Y%m%d')
        self.dateselect = self.dateselect + '0000'
        self.timeselect = target_config['time']
        self.courtselect = target_config['court']
        for i in range(0, len(self.timeselect)):
            self.timeselect[i] = str(self.timeselect[i])

        # read sys configs
        sys_config = json.loads(sys_config_json)
        self.user_agent = str(sys_config['user_agent'])

    logs = ''

    def log(self, line):
        self.logs += line + '<br/>'
        print line

    def giveup(self):
        if self.email:
            Mailer.send([self.email], self.sender,
                        self.subject % (self.success),
                        self.mail_message % (self.eid, self.logs, self.now()),
                        self.reply)
        exit()

    def make_header(self, referer):
        headers = {
            'Referer': referer,
            'User-Agent': self.user_agent
        }
        return headers

    # make request and get response, using Big5 to decode and return html
    def make_request(self, method, url, referer, parameters=None):
        headers = self.make_header(referer)
        r = None
        if method == 'POST':
            if parameters:
                r = requests.post(url, headers=headers,
                                  cookies=self.cookies, data=parameters)
            else:
                r = requests.post(url, headers=headers, cookies=self.cookies)
        elif method == 'GET':
            if parameters:
                r = requests.get(url, headers=headers,
                                 cookies=self.cookies, data=parameters)
            else:
                r = requests.get(url, headers=headers, cookies=self.cookies)
        else:
            return None
        self.cookies.update(r.cookies)
        content = r.content.decode('big5', 'ignore')
        return str(content)

    def request_session_id(self):
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_logon.show'
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_first.show'
        html = self.make_request('POST', url, referer)
        if not html:
            return False
        session_id = Parser.get_session_id(html)
        return session_id

    def login(self):
        # log in
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_logon.show'
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_logon.show'
        parameters = {
            'p_status_code': '',
            'p_sno': '',
            'p_session': self.session_id,
            'p_username': self.eid,
            'p_password': self.password
        }

        html = self.make_request('POST', url, referer, parameters)
        if not html:
            return False
        sid = Parser.get_sid(html)
        if sid:
            self.sid = sid
            return True
        else:
            return False

    def get_dates(self):
        # get dates list
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_book.show'
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_main.' \
            + 'toc?p_session=%s&p_username=%s&p_user_no=/%s/' \
            % (self.session_id, self.eid, self.sid)
        parameters = {
            'p_session': self.session_id,
            'p_username': self.eid,
            'p_user_no': self.sid
        }

        html = self.make_request('POST', url, referer, parameters)
        if not html:
            return False
        request_url = Parser.get_request_url(html)
        if not request_url:
            return False
        user_type = Parser.get_user_type(request_url)
        if not user_type:
            return False
        self.user_type = user_type
        # make second request
        url = request_url
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_book.show' \
            + '?p_session=%s&p_username=%s&p_user_no=/%s/' \
            % (self.session_id, self.eid, self.sid)
        html = self.make_request('GET', url, referer)
        dates = Parser.get_dates(html)
        return dates

    def get_courts(self, date, facility):
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_book_conf.show'
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_opt_fac_types.show'
        parameters = {
            'p_session': self.session_id,
            'p_username': self.eid,
            'p_user_no': self.sid,
            'p_user_type_no': self.user_type,
            'p_alter_adv_ref': '',
            'p_alter_book_no': '',
            'p_enq': '',
            'p_date': date,
            'p_choice': facility
        }
        html = self.make_request('POST', url, referer, parameters)
        if not html:
            return False
        request_url = Parser.get_request_url(html)
        if not request_url:
            return False
        self.booking_referer = request_url
        # make second request
        url = request_url
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_book_conf.show'
        html = self.make_request('GET', url, referer)
        if not html:
            return False
        self.booking_referer = request_url
        booking_parameters = Parser.get_booking_parameters(html)
        if not booking_parameters:
            return False
        self.booking_parameters = booking_parameters
        courts = Parser.get_courts(html)
        return courts

    def make_booking(self, court):
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_conf_msg.show'
        referer = self.booking_referer
        parameters = copy.copy(self.booking_parameters)
        for key in court:
            parameters[key] = court[key]
        html = self.make_request('POST', url, referer, parameters)
        if not html:
            return False
        confirm_no = Parser.get_confirm_no(html)
        if not confirm_no:
            return False
        # confirm
        url = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_conf_msg.show'
        referer = 'http://brazil.cityu.edu.hk:8754/fbi/owa/fbi_web_conf_msg.show'
        parameters = {
            'p_password': self.password,
            'p_username': self.eid,
            'p_sno': confirm_no
        }
        html = self.make_request('POST', url, referer, parameters)
        if not html:
            return False
        message = Parser.get_message(html)
        return Parser.judge_success(message)

    def do(self):
        self.log(API.message('launching'))
        # get session id
        trying_count = 0
        self.log(API.message('try_get_session') % (trying_count + 1,))
        session_id = self.request_session_id()
        while not session_id and trying_count < 100:
            trying_count += 1
            self.log(API.message('fail_get_session'))
            self.log(API.message('try_get_session') % (trying_count + 1,))
            session_id = self.request_session_id()
            time.sleep(1)
        if session_id:
            # print
            self.session_id = session_id
            self.log(API.message('display_session') % (session_id,))
            pass
        else:
            self.log(API.message('fail_get_session'))
            self.log(API.message('give_up'))
            self.giveup()
        # log in
        self.log(API.message('try_log_in') % (self.eid,))
        trying_count = 0
        while not self.login() and trying_count < 5:
            self.log(API.message('fail_log_in'))
            self.log(API.message('try_log_in') % (self.eid,))
            if trying_count == 4:
                self.log(API.message('give_up'))
                # print
                self.giveup()

            trying_count = trying_count + 1

        self.log(API.message('try_get_dates'))
        dates = self.get_dates()
        if self.dateselect not in dates:
            self.log(API.message('date_not_avail') % (self.dateselect,))
            self.log(API.message('give_up'))
            # not bookable
            self.giveup()

        trying_count = 0
        success = False
        while not success and trying_count < 10:
            self.log(API.message('try_get_avail') % (self.dateselect, self.choice,
                trying_count + 1))
            courts = self.get_courts(self.dateselect, self.choice)
            if str(courts).startswith('alert'):
                self.log(API.now() + str(courts)[5:])
                self.log(API.message('give_up'))
                self.giveup()
            if len(courts) == 0:
                self.log(API.message('no_courts_at_all') % (self.dateselect, self.choice))
                self.log(API.message('give_up'))
                self.giveup()
            # time first
            for pstime in self.timeselect:
                self.log(API.message('try_time') % (pstime,))
                for pcourt in self.courtselect:
                    # see whether best court
                    self.log(API.message('try_court') % (pcourt,))
                    for court in courts:
                        if int(court['p_stime']) == int(pstime) and \
                            court['p_court'] == pcourt:
                            self.log(API.message('try_book') % (pcourt, pstime))
                            if self.make_booking(court):
                                self.success = 'SUCCESS'
                                self.log(API.message('success'))
                                success = True
                                break
                    if success:
                        break
                if success:
                    break
                # try other court
                self.log(API.message('try_other_court'))
                for court in courts:
                    if int(court['p_stime']) == int(pstime):
                        self.log(API.message('try_book') % (court['p_court'], pstime))
                        if self.make_booking(court):
                            self.success = 'SUCCESS'
                            self.log(API.message('success'))
                            success = True
                            break
                if success:
                    break
            trying_count += 1
            if not success:
                self.log(API.message('fail_book'))
        self.giveup()


