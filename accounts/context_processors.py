from bson.objectid import ObjectId
from django.conf import settings
from pymongo import MongoClient



# EDIT: Count records from the same MongoDB collection used by the notification
# views, so the navigation bell immediately reflects newly inserted alerts.
# EDIT: Resolve the session's Django id to the matching MongoDB auth_user _id
# so the bell count sees both legacy and newly created notifications.
def _notification_id_variants(db, user_id):
    variants = [user_id, str(user_id)]
    if str(user_id).isdigit():
        variants.append(int(user_id))
    if ObjectId.is_valid(str(user_id)):
        variants.append(ObjectId(str(user_id)))
    user = db['auth_user'].find_one({
        '$or': [{'id': {'$in': variants}}, {'_id': {'$in': variants}}]
    })
    if user:
        variants.extend([user.get('id'), user.get('_id'), str(user.get('id')), str(user.get('_id'))])
    return [value for value in variants if value is not None]

def _navbar_notifications(request):
    """Share one bounded preview/count result across registered processors."""
    if not hasattr(request, "_edu_notification_context"):
        from .notification_services import get_user_notification_center
        request._edu_notification_context = get_user_notification_center(request.user)
    return request._edu_notification_context


def unread_notifications(request):
    return {
        **_navbar_notifications(request),
        'can_manage_configuration': _can_manage_configuration(request),
        'can_manage_fee_categories': _has_role(
            request, {'Super Admin', 'Super Administrator'},
        ),
    }


def _has_role(request, permitted_roles):
    """Resolve roles from Django and legacy MongoDB group links."""
    user = request.user
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=permitted_roles).exists():
        return True

    # Also support legacy user/group links that were written directly to
    # MongoDB with a different identifier representation.
    try:
        client = MongoClient(
            settings.MONGO_URI if hasattr(settings, 'MONGO_URI')
            else settings.DATABASES['default']['CLIENT']['host']
        )
        db = client[settings.DATABASES['default']['NAME']]
        user_ids = _notification_id_variants(db, user.pk)
        group_ids = [
            link.get('group_id')
            for link in db['auth_user_groups'].find({'user_id': {'$in': user_ids}})
        ]
        return db['auth_group'].count_documents({
            '$and': [
                {'$or': [{'id': {'$in': group_ids}}, {'_id': {'$in': group_ids}}]},
                {'name': {'$in': list(permitted_roles)}},
            ]
        }) > 0
    except Exception:
        return False


def _can_manage_configuration(request):
    """Expose the configuration-nav entitlement to every base template."""
    return _has_role(
        request,
        {'Super Admin', 'Super Administrator', 'School Administrator'},
    )
def notification_badge(request):
    return _navbar_notifications(request)
