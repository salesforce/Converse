# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


from wrapt_timeout_decorator import timeout
from Converse.utils.utils import resp


@timeout(0.1)
def funcInch2Cm(entities, *argv, **kargs):
    return resp(True, "The Inch to Cm function is from the additional functions")


@timeout(0.1)
def additional_function_test(entities, *argv, **kargs):
    return resp(True, "This is the return value of a test additional function")
