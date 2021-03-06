import json
import oauth2 as oauth

import endpoints
from .exceptions import LinkedInException
from helpers import args_to_dict
from helpers import build_url_with_qs
from helpers import date_to_str

PROFILE_ARGS = ','.join(['first-name','last-name','id','picture-url','public-profile-url'])


class LinkedIn(object):
    def __init__(self, consumer_key=None, consumer_secret=None,
                 oauth_token=None, oauth_secret=None):
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)
        self.token = oauth.Token(oauth_token, oauth_secret)
        self.client = oauth.Client(self.consumer, self.token)

    def get_group_memberships(self):
        url = endpoints.GROUP_MEMBERSHIPS
        return self._make_request(url)

    def get_group_posts(self, group_id, start=0, count=10, order='recency',
                        role=None, modified_since=None):
        if order not in ('recency', 'popularity'):
            raise ValueError('Sort order must be either recency or popularity')
        _args = {'modified-since': modified_since}
        args = args_to_dict(start=start, count=count, order=order, role=role,
                            **_args)
        base = endpoints.GROUP_FEED.format(group_id=group_id)
        url = build_url_with_qs(base, args)
        return self._make_request(url)

    def create_group_post(self, group_id, title, summary):
        args = args_to_dict(title=title, summary=summary)
        body = json.dumps(args)
        url = endpoints.CREATE_POST.format(group_id=group_id)
        return self._make_request(url, method='POST', body=body)

    def delete_group_post(self, post_id):
        url = endpoints.DELETE_POST.format(post_id=post_id)
        return self._make_request(url, method='DELETE')

    def get_comments_for_post(self, post_id, count=10, start=0):
        args = args_to_dict(count=count, start=start)
        base = endpoints.POST_COMMENTS.format(post_id=post_id)
        url = build_url_with_qs(base, args)
        return self._make_request(url)

    def create_comment(self, post_id, text):
        args = args_to_dict(text=text)
        body = json.dumps(args)
        url = endpoints.CREATE_COMMENT.format(post_id=post_id)
        return self._make_request(url, method='POST', body=body)

    def delete_comment(self, comment_id):
        url = endpoints.DELETE_COMMENT.format(comment_id=comment_id)
        return self._make_request(url, method='DELETE')

    def like_post(self, post_id):
        return self._like_unlike_post(post_id, True)

    def unlike_post(self, post_id):
        return self._like_unlike_post(post_id, False)

    def _like_unlike_post(self, post_id, is_liked):
        body = json.dumps(is_liked) #json true/false
        url = endpoints.LIKE_POST.format(post_id=post_id)
        return self._make_request(url, method='PUT', body=body)

    def get_network_updates(self, update_type=None, before=None, after=None,
                            count=10, start=0):
        update_type = update_type or []
        if not isinstance(update_type, (list, tuple, basestring)):
            raise TypeError('update_type must be a list or a string')
        if before:
            before = date_to_str(before)
        if after:
            after = date_to_str(after)
        args = args_to_dict(type=update_type, before=before, after=after,
                            count=count, start=start)
        url = build_url_with_qs(endpoints.NETWORK_UPDATES, args)
        return self._make_request(url)

    def get_profile(self, member_id=None):
        if member_id is None:
            url = "%s/~:(%s)" % (endpoints.PROFILE, PROFILE_ARGS)
        else:
            url = "%s/id=%s:(%s)" % (endpoints.PROFILE, member_id, PROFILE_ARGS)
        return self._make_request(url)

    def _make_request(self, uri, method='GET', body=''):
        headers = {'x-li-format': 'json'}
        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/json'

        resp, content = self.client.request(uri, method=method,
                                            headers=headers, body=body)
        if resp['status'] == '200':
            return json.loads(content)
        elif resp['status'] in ('201', '204'):
            return True
        else:
            #TODO: more sophisticated error handling
            raise LinkedInException('API call failed with status: %s' %
                                    resp['status'])

