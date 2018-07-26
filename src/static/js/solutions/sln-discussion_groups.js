/*
 * Copyright 2018 Mobicage NV
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @@license_version:1.3@@
 */

'use strict';
var discussionGroups = [];
var loaded = {};

function getDiscussionGroups(callback) {
    if (loaded.discussionGroups) {
        callback(discussionGroups);
    } else {
        loadDiscussionGroups(function () {
            loaded.discussionGroups = true;
            callback(discussionGroups);
        });
    }
}

function loadDiscussionGroups(callback) {
    sln.call({
        url: '/common/discussion_groups/list',
        method: 'get',
        success: function (data) {
            discussionGroups = data;
            callback(discussionGroups);
        }
    });
}

function getDiscussionGroup(groupId, callback) {
    groupId = parseInt(groupId);
    getDiscussionGroups(function (groups) {
        var group = groups.filter(function (g) {
            return g.id === groupId;
        })[0];
        callback(group);
    });
}

function putDiscussionGroup(discussionGroup) {
    sln.call({
        url: '/common/discussion_groups',
        data: {
            discussion: discussionGroup
        },
        method: 'post',
        success: function (data) {
            getDiscussionGroup(discussionGroup.id, function () {
                if (discussionGroup.id) {
                    discussionGroup = data;
                } else {
                    discussionGroups.push(data);
                }
                window.location.hash = '#/discussion_groups';
            });
        },
        error: function (data) {
            if (data.status === 404) {
                sln.alert(CommonTranslations.could_not_find_discussion_group, null, CommonTranslations.ERROR);
            } else {
                sln.showAjaxError();
            }
        }
    });
}

function deleteDiscussionGroup(groupId) {
    getDiscussionGroup(groupId, function (group) {
        var text = CommonTranslations.confirm_delete_discussion_group.replace('%(topic)s', group.topic);
        sln.confirm(text, doDelete, abortDelete, CommonTranslations.YES, CommonTranslations.NO);

        function abortDelete() {
            window.location.hash = '#/discussion_groups';
        }

        function doDelete() {
            sln.call({
                url: '/common/discussion_groups/delete',
                data: {
                    discussion_group_id: groupId
                },
                method: 'post',
                success: function () {
                    getDiscussionGroup(groupId, function (group) {
                        discussionGroups.splice(discussionGroups.indexOf(group), 1);
                    });
                    window.location.hash = '#/discussion_groups';
                },
                error: function (data) {
                    if (data.status === 404) {
                        sln.alert(CommonTranslations.could_not_find_discussion_group, null, CommonTranslations.ERROR);
                    } else {
                        sln.showAjaxError();
                    }
                }
            });
        }
    });
}

function renderPutDiscussionGroup(groupId) {
    getDiscussionGroup(groupId, function (group) {
        var html = $.tmpl(templates['discussion_groups/discussion_groups_put'], {
            group: group || {},
            T: CommonTranslations
        });
        $('#discussion_groups_content').html(html);
        $('#put_discussion_group').click(function () {
            if (!group) {
                group = {};
            }
            $('[id^=dg_]').each(function (i, elem) {
                var $elem = $(elem);
                group[$elem.attr('id').replace('dg_', '')] = $elem.val();
            });
            putDiscussionGroup(group);
        });
    });
}
function renderDiscussionGroups() {
    getDiscussionGroups(function (groups) {
        var html = $.tmpl(templates['discussion_groups/discussion_groups_list'], {
            groups: groups,
            T: CommonTranslations,
            formatTime: sln.format
        });
        $('#discussion_groups_content').html(html);
    });
}
