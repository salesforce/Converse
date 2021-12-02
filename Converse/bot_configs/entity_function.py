from wrapt_timeout_decorator import timeout
from Converse.utils.utils import resp


@timeout(0.5)
def myfunction(entities, *argv, **kargs):
    """
    A function template.
    If you would like to create your own entity function, it should look like this.
    """
    entity_name = "some_entity_name"
    try:
        my_entity_value = some_operation(entities[entity_name])
        success = True
        message = (
            "This is the response for my entity, the entity value is {}".format(
                my_entity_value
            ),
        )
    except:
        print("Could not process the entity.")
        success = False
        message = "This is the response when I cannot process the entity."
    return resp(success, message)
