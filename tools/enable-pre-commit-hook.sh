#!/bin/bash
# Copyright (c) 2015 Aptira Pty Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


PRE_COMMIT_SCRIPT=.git/hooks/pre-commit

make_hook() {
    echo "exec ./run_tests.sh -N -p" >> $PRE_COMMIT_SCRIPT
    chmod +x $PRE_COMMIT_SCRIPT

    if [ -w $PRE_COMMIT_SCRIPT -a -x $PRE_COMMIT_SCRIPT ]; then
        echo "pre-commit hook was created successfully"
    else
        echo "unable to create pre-commit hook"
    fi
}

# NOTE(Bharat): Make sure we are in guts root directory before adding the hook.
if [ ! -d ".git" ]; then
    echo "Unable to find .git; Moving up a directory"
    cd ..
    if [ -d ".git" ]; then
        make_hook
    else
        echo "Still unable to find .git; hook not created"
    fi
else
    make_hook
fi
