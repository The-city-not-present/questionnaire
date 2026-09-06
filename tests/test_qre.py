
import sys
import os


# if os.environ.get("PYCHARM_HOSTED") == "1":
#     sys.path.insert(0,"/Users/andrej/.../src/lib/qre")


from src import (
    # LocalizedText,
    ValidationError,
    Category,
    Question,
    QuestionModifierIsExclusive,
    QuestionTypeBlock,
    QuestionTypeBool,
    QuestionTypeCompound,
    QuestionTypeDatetime,
    QuestionTypeFloat,
    QuestionTypeInt,
    QuestionTypeLoop,
    QuestionTypeMultiPunch,
    QuestionTypePlain,
    QuestionTypeRoot,
    QuestionTypeSinglePunch,
    QuestionTypeText,
)
from src.to_schema import question_to_schema as to_schema



def create_example_qre():
    return QuestionTypeRoot(
        label = 'Disney study',
        fields = [
            QuestionTypeBlock(
                name = 'screener',
                label = None,
                fields = [
                    QuestionTypeBool(
                        name='consent',
                        label='''Welcome and thank you for your interest!

The contents of this study are confidential and may not be shared...

I understand that my personal information...
''',
                    ),
                    QuestionTypeInt(
                        name='yearborn',
                        label='Please type in the year you were born.',
                    ),
                    QuestionTypeSinglePunch(
                        name='gender',
                        label='Please select your gender.',
                        categories=set(
                            Category(
                                name=record.get('name'),
                                label=record.get('label'),
                            ) for record in (
                                {'name': 'male', 'label': 'Male', },
                                {'name': 'female', 'label': 'Female', },
                                {'name': 'nonbinary', 'label': 'Other not listed', },
                            )
                        ),
                        helper_fields=[
                            QuestionTypeText(
                                name='otherspec',
                                label='Other:',
                            ),
                        ],
                    ),
                ],
            ),
            QuestionTypeBlock(
                name='main',
                label=None,
                fields=[
                    QuestionTypeMultiPunch(
                        name='aidedaware',
                        label='''Which of these video streaming services...
        ''',
                        categories=set([
                            Category(
                                name='disneyplus',
                                label='Disney+',
                                properties={ 'value': 1, },
                            ),
                            Category(
                                name='hulu',
                                label='Hulu',
                                properties={'value': 2, },
                            ),
                            Category(
                                name='netflix',
                                label='Netflix',
                                properties={'value': 3, },
                            ),
                            Category(
                                name='noneofthese',
                                label='None of the above',
                                properties={'value': 99, },
                            ),
                        ]),
                        modifiers=[
                            QuestionModifierIsExclusive(
                                data=[
                                    Category(
                                        name='noneofthese',
                                        label=None,
                                    ),
                                ],
                            )
                        ],
                    ),
                    QuestionTypeText(
                        name='openend',
                        label='What other streaming services come to mind?',
                        is_required=False,
                    )
                ],
            ),
        ],
    )


def create_example_received_data():
    return {
        'screener': {
            'yearborn': 1915,
            'gender': 'male',
            'gender.:helperfields': {
                'otherspec': 'no comment',
            },
            'consent': True,
        },
        'main': {
            'aidedaware': ['disneyplus','noneofthese'],
        }
    }


def test_basic():
    qre = create_example_qre()
    schema = to_schema(qre)
    received_data = create_example_received_data()
    try:
        qre.assign(received_data,None)
    except ValidationError as e:
        validation_err_message = e.args[0]
        validation_err_path = e.path
        print((validation_err_message,validation_err_path,),file=sys.stderr)
        raise e

def test_wrongtype_other():
    qre = create_example_qre()
    schema = to_schema(qre)
    received_data = create_example_received_data()
    received_data['screener']['gender.:helperfields'] = { 'otherspec': 2, }
    try:
        qre.assign(received_data,None)
    except ValidationError as e:
        validation_err_message = e.args[0]
        validation_err_path = e.path
        print((validation_err_message,validation_err_path,),file=sys.stderr)
        if validation_err_path == 'screener.gender.:helperfields.otherspec':
            return None
        raise e
    raise Exception('No validation issue caught')

def test_missing_other():
    qre = create_example_qre()
    schema = to_schema(qre)
    received_data = create_example_received_data()
    del received_data['screener']['gender.:helperfields']
    try:
        qre.assign(received_data,None)
    except ValidationError as e:
        validation_err_message = e.args[0]
        validation_err_path = e.path
        if validation_err_path == 'screener.gender.:helperfields.otherspec':
            return None
        raise e
    raise Exception('No validation issue caught')

