from dataclasses import dataclass, field
# from collections.abc import Iterable
import copy

from .question_types import (
    Question,
    Category,
    InternalError,
    ValidationError,
    QuestionTypeBlock,
    QuestionTypeLoop,
)


def validate_names(fields):
    if not all(f._validate_name() for f in fields):
        raise InternalError('name validation failed')
    names = [f.name for f in fields]
    if len(names) != len(set(names)):
        raise InternalError('name validation failed')
    return True


def json_schema_items_ordered(fields: dict) -> dict:
    return {
        f_name: {
            **f_obj,
            "x-ui": {
                **f_obj.get("x-ui",{}),
                "order": i,
            },
        } for i, (f_name, f_obj) in enumerate(fields.items())
    }


def make_validation_rules(question):
    return None # TODO:





def question_to_schema(question_instance: Question) -> dict:
    def transform_helperfield_name(question_instance):
        question = copy.copy(question_instance)
        question.name = f':helperfields.{question.name}'
        return question
    @dataclass
    class CategoryElementClass(Question):
        category: Category = field(kw_only=True)
        fields: list[Question] = field(kw_only=True)
        def get_type_str(self) -> str:
            return 'iteration'
        def validate(self, data) -> bool:
            return all(f.validate(data.get(f.name)) for f in self.fields)
        def assign(self, data) -> Question:
            if not self.validate(data):
                raise ValidationError('Validation failed')
            for f in self.fields:
                if f.name in data:
                    f.assign(data.get(f.name))
            self._assign_helper_fields(data.get(':helperfields',{}))
            return self

    question = copy.copy(question_instance) # for safety, to not occasionally modify

    if hasattr(question, 'fields') and question.fields:
        validate_names(question.fields)
    if hasattr(question, 'helper_fields') and question.helper_fields:
        validate_names(question.helper_fields)

    if isinstance(question, CategoryElementClass):
        result = {
            "type": "object",
            "title": str(question.category.label),
            "properties": {
                f.name: question_to_schema(f) for f in question.fields
            },
            "x-ui": {
                **{key: value for mod in question.modifiers for key, value in mod.as_json().items()},
            },
            "x-properties": question.properties,
        }
        result['properties'] = json_schema_items_ordered(result.get('properties', {}))
        return result

    # make up the fields
    question_fields = []
    if isinstance(question, QuestionTypeBlock):
        # if block
        question_fields = question.fields
    elif isinstance(question, QuestionTypeLoop):
        # if loop
        def make_field(question,cat_key,field_index,default_spec):
            if cat_key not in question.response:
                question.response[cat_key] = [copy.deepcopy(f) for f in question.fields]
            response_slice = question.response.get(cat_key)
            f: Question = response_slice[field_index]
            f.update(default_spec)
            return f
        question_fields = [
            CategoryElementClass(
                name = cat.name,
                label = cat.label,
                properties = cat.properties,
                modifiers = cat.modifiers,
                widget = None,
                helper_fields = {},
                category = cat,
                fields = [ make_field(question,cat.name,i,f) for i,f in enumerate(question.fields) ],
            ) for cat in question.iterations
        ]
    elif hasattr(question, 'fields') and question.fields:
        # if other - hmm, I don't have anything other in design
        raise InternalError('Unrecognized question type: has "fields" attr but is not block or loop')

    if hasattr(question, 'helper_fields') and question.helper_fields:
        question_fields.extend([transform_helperfield_name(f) for f in question.helper_fields])

    result = {
        "type": "object" if not question.is_plain else question.get_type_str(),
        "title": str(question.label),
        "properties": {
            f.name: question_to_schema(f) for f in question_fields
        },
        "x-type": question.get_type_str(),
        "x-validation-rules": make_validation_rules(question),
        "x-widget": question.widget,
        "x-ui": {
            **{ key: value for mod in question.modifiers for key, value in mod.as_json().items() },
        },
        "x-properties": question.properties,
    }
    result['properties'] = json_schema_items_ordered(result.get('properties', {}))
    return result
