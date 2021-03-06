# -*- coding:utf8 -*-
import functools
import textwrap
import datetime
import boto3
from errbot import BotPlugin, botcmd, arg_botcmd


# TODO: Duplicated inmplements
def require_iam(f):
    """Deforator for bot command required IAM user key pair
    """
    @functools.wraps(f)
    def _require_iam(bot, msg, args):
        if not bot.config \
                or not bot.config.get('access_id', None) \
                or not bot.config.get('secret_key', None):
            return bot.not_configured()
        return f(bot, msg, args)
    return _require_iam


class Route53(BotPlugin):
    """
    Control Route 53
    """
    # TODO: Duplicated inmplements
    def has_iam(self):
        return self.config \
                and self.config.get('access_id', False) \
                and self.config.get('secret_key', False)

    def not_configured(self):
        message = """
            This plugin is until not configured.
            Please call `{}plugin config route53` to read format,
            And set your configurations.
            """
        return textwrap.dedent(message).format(self.bot_config.BOT_PREFIX)

    def get_configuration_template(self):
        """
        Defines the configuration structure this plugin supports.
        """
        config = {
            'access_id': None,
            'secret_key': None,
        }
        return config

    def get_client(self):
        """Return CloudFront client by boto3.
        This client is configuret by plugin configuration.
        """
        return boto3.client(
            'route53',
            aws_access_key_id=self.config['access_id'],
            aws_secret_access_key=self.config['secret_key'],
        )

    @botcmd(template='zone_list')
    @require_iam
    def route53_list(self, msg, args):
        client = self.get_client()
        result = client.list_hosted_zones()
        return {'zones': result['HostedZones']}

    @arg_botcmd('zone_id', template='zone_detail')
    def route53_zone(self, msg, zone_id):
        if not self.has_iam():
            return self.not_configured()
        client = self.get_client()
        result = client.list_resource_record_sets(HostedZoneId=zone_id)
        return {'records': result['ResourceRecordSets']}

    @arg_botcmd('hostname', template='zone_created')
    def route53_create(self, msg, hostname):
        if not self.has_iam():
            return self.not_configured()
        client = self.get_client()
        result = client.create_hosted_zone(
            Name=hostname,
            CallerReference='new_zone-{}'.format(
                datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            ),
        )
        zone_info = result['HostedZone']
        zone_info['NameServers'] = result['DelegationSet']['NameServers']
        return {'zone_info': zone_info}

    @arg_botcmd('record_value')
    @arg_botcmd('record_type')
    @arg_botcmd('name')
    @arg_botcmd('zone_id')
    def route53_add_record(self, msg, zone_id, name, record_type, record_value):
        if record_type not in ['A', 'CNAME']:
            return 'Only A or CNAME record'
        if not self.has_iam():
            return self.not_configured()
        zone_id = zone_id[12:]
        client = self.get_client()
        result = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Comment': 'Add new record',
                'Changes': [
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': name,
                            'Type': record_type,
                            'TTL': 300,
                            'ResourceRecords': [
                                {'Value': record_value}
                            ],
                        }
                    }
                ]
            }
        )
        return 'Now creating'
