# -*- coding:utf8 -*-
from unittest.mock import patch
import textwrap
import time


pytest_plugins = [
    'errbot.backends.test',
]
extra_plugin_dir = '.'


def inject_dummy_conf(bot):
    bot.push_message('!plugin config route53 '\
        '{"access_id":"1","secret_key":"1"}')
    bot.pop_message()


def test_installed_plugin(testbot):
    testbot.push_message('!status plugins')
    assert 'route53' in testbot.pop_message()


def test_not_configured(testbot):
    testbot.push_message('!route53_list')
    assert 'This plugin is until not configured' \
        in testbot.pop_message()


def test_list_configured(testbot):
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.list_hosted_zones.return_value = {
            'HostedZones': [
                {
                    'Id': 'zone-id',
                    'Name': 'example.com',
                    'Config': {
                        'Comment': 'My zone',
                        'PrivateZone': False,
                    },
                    'ResourceRecordSetCount': 123
                },
            ],
        }
        testbot.push_message('!route53 list')
        assert 'example.com' in testbot.pop_message()


def test_detail_single(testbot):
    import textwrap
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': [
                {
                    'Name': 'a.example.com',
                    'Type': 'A',
                    'ResourceRecords': [
                        {
                            'Value': '127.0.0.1'
                        },
                    ],
                },
            ],
        }
        testbot.push_message('!route53 zone ABCDEF')
        expect = """
            - a.example.com : A
                - 127.0.0.1
            """
        assert textwrap.dedent(expect).strip() \
            in testbot.pop_message()


def test_detail_multi_values(testbot):
    import textwrap
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': [
                {
                    'Name': 'a.example.com',
                    'Type': 'A',
                    'ResourceRecords': [
                        {'Value': '127.0.0.1'},
                        {'Value': '127.0.0.2'},
                    ],
                },
            ],
        }
        testbot.push_message('!route53 zone ABCDEF')
        expect = """
            - a.example.com : A
                - 127.0.0.1
                - 127.0.0.2
            """
        assert textwrap.dedent(expect).strip() \
            in testbot.pop_message()


def test_detail_multi_records(testbot):
    import textwrap
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': [
                {
                    'Name': 'a.example.com',
                    'Type': 'A',
                    'ResourceRecords': [
                        {'Value': '127.0.0.1'},
                    ],
                },
                {
                    'Name': 'b.example.com',
                    'Type': 'A',
                    'ResourceRecords': [
                        {'Value': '127.0.0.2'},
                    ],
                },
            ],
        }
        testbot.push_message('!route53 zone ABCDEF')
        expect = """
            - a.example.com : A
                - 127.0.0.1
            - b.example.com : A
                - 127.0.0.2
            """
        assert textwrap.dedent(expect).strip() \
            in testbot.pop_message()


def test_create(testbot):
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.create_hosted_zone.return_value = {
            'HostedZone': {
                'Id': 'ABCDEF',
                'Name': 'example.com',
                'CallerReference': 'string',
            },
            'DelegationSet': {
                'Id': 'string',
                'CallerReference': 'string',
                'NameServers': [
                    '127.0.0.1',
                    '127.0.0.2',
                ]
            },
        }
        testbot.push_message('!route53 create example.com')
        expect = """
            - 127.0.0.1
            - 127.0.0.2
            """
        actually = testbot.pop_message()
        assert testbot.bot.md.convert(textwrap.dedent(expect)) \
            in actually
        assert 'example.com' in actually
        assert 'ABCDEF' in actually


def test_add_record(testbot):
    inject_dummy_conf(testbot)
    with patch('boto3.client') as Client:
        client = Client.return_value
        client.change_resource_record_sets.return_value = {
            'ChangeInfo': {
                'Id': 'ABCDEF',
                'Name': 'example.com',
                'CallerReference': 'string',
            },
        }
        testbot.push_message('!route53 add_record ABCDEF www.example.com A 127.0.0.1')
        actually = testbot.pop_message()
        assert 'Now creating' \
            in actually
