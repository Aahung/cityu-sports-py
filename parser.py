__author__ = 'Hung'

from bs4 import BeautifulSoup


class Parser(object):
    """docstring for Parser"""
    @staticmethod
    def get_session_id(html):
        bs = BeautifulSoup(html)
        try:
            session_input = bs.select('input[name="p_session"]')
            session_id = str(session_input[0].get('value'))
            return session_id
        except Exception:
            return None

    @staticmethod
    def get_sid(html):
        bs = BeautifulSoup(html)
        try:
            main_win = bs.select('frame[name="main_win"]')
            user_info = str(main_win[0].get('src'))
            user_info_tokens = user_info.split('&')
            for user_info_token in user_info_tokens:
                if 'p_user_no' in user_info_token:
                    tokens = user_info_token.split('/')
                    if len(tokens) > 1:
                        return tokens[1]
            return None
        except Exception:
            return None

    @staticmethod
    def get_request_url(html):
        tokens = []
        if 'opt_left_win' in html:
            tokens = html.split('" NAME="opt_left_win"')
        else:
            tokens = html.split('" NAME="body_win"')
        if len(tokens) > 0:
            tokens = tokens[0].split('<FRAME SRC="')
            if len(tokens) > 0:
                link = tokens[-1]
                url = 'http://brazil.cityu.edu.hk:8754%s' % (link,)
                return url
        return None

    @staticmethod
    def get_user_type(request_url):
        tokens = request_url.split('p_user_type_no=')
        if len(tokens) > 1:
            tokens = tokens[1].split('&')
            if len(tokens) > 0:
                return tokens[0]
        return None

    @staticmethod
    def get_dates(html):
        dates = []
        bs = BeautifulSoup(html)
        try:
            links = bs.select('a')
            for link in links:
                href = link.get('href')
                if href:
                    href = str(href)
                    tokens = href.split('date_data(\'')
                    if len(tokens) < 1:
                        continue
                    date = tokens[1]
                    if '\',\'' in date:
                        tokens = date.split('\',\'')
                    else:
                        tokens = date.split('&#39')
                    if len(tokens) < 1:
                        continue
                    date = tokens[0]
                    dates.append(date)
            return dates
        except Exception:
            return None

    @staticmethod
    def get_courts(html):
        courts = []
        bs = BeautifulSoup(html)
        try:
            links = bs.select('a')
            for link in links:
                imgs = link.select('img')
                if len(imgs) == 0:
                    continue
                img = imgs[0]
                tokens = []
                if img.get('src') and img.get('src') == \
                        '/pebook-img/sq_cyan.gif':
                    href = str(link.get('href'))
                    if 'alert' in href:
                        return 'alert' + href.split('alert(\'')[1]
                    tokens = href.split('sub_data')
                    if len(tokens) < 2:
                        continue
                    string = tokens[1]
                    string = string.replace('(', '').replace(')', '')
                    string = string.replace(';', '').replace('&#39', '')
                    string = string.replace('\'', '')
                    tokens = string.split(',')
                    if len(tokens) > 4:
                        court = {
                            'p_date': tokens[0],
                            'p_court': tokens[1],
                            'p_venue': tokens[2],
                            'p_facility_ref': tokens[3],
                            'p_stime': tokens[4]
                        }
                        courts.append(court)
            return courts
        except Exception, ex:
            return None

    @staticmethod
    def get_booking_parameters(html):
        booking_parameters = {}
        bs = BeautifulSoup(html)
        try:
            inputs = bs.select('input[type="hidden"]')
            for input in inputs:
                name = str(input.get('name'))
                value = str(input.get('value'))
                booking_parameters[name] = value
            return booking_parameters
        except Exception, ex:
            return None

    @staticmethod
    def get_message(html):
        bs = BeautifulSoup(html)
        try:
            text = ''
            smalls = bs.select('small')
            if len(smalls) > 0:
                for small in smalls:
                     text += small.text + ' '
                return text
            return None
        except Exception:
            return None

    @staticmethod
    def get_confirm_no(html):
        tokens = html.split('NAME="p_sno" VALUE="')
        if len(tokens) > 1:
            tokens = tokens[1].split('"')
            return tokens[0]

    @staticmethod
    def judge_success(message):
        if 'reserved' in message:
            return True
        return False

