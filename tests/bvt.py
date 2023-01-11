from nvmetools import TestCase, TestStep, TestSuite, rqmts

def verify_stop_on_fail():
    for suite_sof in [True, False]:
        for test_sof in [True, False]:
            for step_sof in [True, False]:
                print("\nverify stop on fail")
                print(f"  suite: {suite_sof}")
                print(f"  test:  {test_sof}")
                print(f"  step:  {step_sof}\n")

                with TestSuite("bvt stop on fail") as suite:
                    suite.create_reports=False
                    suite.stop_on_fail=suite_sof

                    with TestCase(suite, "Test1") as test:
                        test.stop_on_fail = test_sof

                        with TestStep(test, "Step") as step:
                            step.stop_on_fail = step_sof
                            rqmts._force_pass(step)
                            rqmts._force_fail(step)
                            rqmts._force_pass(step)

                        with TestStep(test, "Step2") as step:
                            rqmts._force_pass(step)

                    with TestCase(suite, "Test2") as test:
                        with TestStep(test, "Step") as step:
                            rqmts._force_pass(step)

                if suite_sof:
                    assert suite.state['summary']['tests']['total'] == 1
                    assert suite.state['summary']['tests']['pass'] == 0
                    assert suite.state['summary']['tests']['fail'] == 1

                    if test_sof:
                        if step_sof:
                            assert suite.state['summary']['verifications']['total'] == 2
                        else:
                            assert suite.state['summary']['verifications']['total'] == 3
                    else:
                        if step_sof:
                            assert suite.state['summary']['verifications']['total'] == 3
                        else:
                            assert suite.state['summary']['verifications']['total'] == 4
                else:
                    assert suite.state['summary']['tests']['total'] == 2
                    assert suite.state['summary']['tests']['pass'] == 1
                    assert suite.state['summary']['tests']['fail'] == 1

                    if test_sof:
                        if step_sof:
                            assert suite.state['summary']['verifications']['total'] == 3
                        else:
                            assert suite.state['summary']['verifications']['total'] == 4
                    else:
                        if step_sof:
                            assert suite.state['summary']['verifications']['total'] == 4
                        else:
                            assert suite.state['summary']['verifications']['total'] == 5


def verify_step_stop():
    for force_fail in [True, False]:
        for fail_rqmt in [True, False]:

            print("\nverify step stop")
            print(f"  force fail:  {force_fail}")
            print(f"  failed rqmt:  {fail_rqmt}")

            with TestSuite("bvt step stop") as suite:
                suite.create_reports=False

                with TestCase(suite, "Test1") as test:

                    with TestStep(test, "Step") as step:
                        step.stop_on_fail = False

                        rqmts._force_pass(step)

                        if fail_rqmt: rqmts._force_fail(step)
                        step.stop(force_fail=force_fail)
                        rqmts._force_pass(step)
                        rqmts._force_pass(step)

                    with TestStep(test, "Step2") as step:
                        rqmts._force_pass(step)

            assert suite.state['summary']['tests']['total'] == 1

            if force_fail:
                assert suite.state['summary']['tests']['fail'] == 1
                assert suite.state['summary']['tests']['pass'] == 0
                if fail_rqmt:
                    assert suite.state['summary']['verifications']['total'] == 3
                else:
                    assert suite.state['summary']['verifications']['total'] == 2
            else:
                if fail_rqmt:
                    assert suite.state['summary']['tests']['fail'] == 1
                    assert suite.state['summary']['tests']['pass'] == 0
                    assert suite.state['summary']['verifications']['total'] == 3
                else:
                    assert suite.state['summary']['tests']['fail'] == 0
                    assert suite.state['summary']['tests']['pass'] == 1
                    assert suite.state['summary']['verifications']['total'] == 2


def verify_test_stop():
    for force_fail in [True, False]:
        for fail_rqmt in [True, False]:

            print("\nverify test stop")
            print(f"  force fail:  {force_fail}")
            print(f"  failed rqmt:  {fail_rqmt}")

            with TestSuite("bvt test stop") as suite:
                suite.create_reports=False

                with TestCase(suite, "Test1") as test:

                    with TestStep(test, "Step") as step:
                        step.stop_on_fail = False

                        rqmts._force_pass(step)

                        if fail_rqmt: rqmts._force_fail(step)
                        test.stop(force_fail=force_fail)
                        rqmts._force_pass(step)
                        rqmts._force_pass(step)

                    with TestStep(test, "Step2") as step:
                        rqmts._force_pass(step)

            assert suite.state['summary']['tests']['total'] == 1

            if force_fail:
                assert suite.state['summary']['tests']['fail'] == 1
                assert suite.state['summary']['tests']['pass'] == 0
                if fail_rqmt:
                    assert suite.state['summary']['verifications']['total'] == 2
                else:
                    assert suite.state['summary']['verifications']['total'] == 1
            else:
                if fail_rqmt:
                    assert suite.state['summary']['tests']['fail'] == 1
                    assert suite.state['summary']['tests']['pass'] == 0
                    assert suite.state['summary']['verifications']['total'] == 2
                else:
                    assert suite.state['summary']['tests']['fail'] == 0
                    assert suite.state['summary']['tests']['pass'] == 1
                    assert suite.state['summary']['verifications']['total'] == 1


def verify_suite_stop():
    for force_fail in [True, False]:
        for fail_rqmt in [True, False]:

            print("\nverify suite stop")
            print(f"  force fail:  {force_fail}")
            print(f"  failed rqmt:  {fail_rqmt}")

            with TestSuite("bvt suite stop") as suite:
                suite.create_reports=False

                with TestCase(suite, "Test1") as test:

                    with TestStep(test, "Step") as step:
                        step.stop_on_fail = False

                        rqmts._force_pass(step)

                        if fail_rqmt: rqmts._force_fail(step)
                        suite.stop(force_fail=force_fail)
                        rqmts._force_pass(step)
                        rqmts._force_pass(step)

                    with TestStep(test, "Step2") as step:
                        rqmts._force_pass(step)

            assert suite.state['summary']['tests']['total'] == 1

            if force_fail:
                assert suite.state['result'] == 'FAILED'
                if fail_rqmt:
                    assert suite.state['summary']['verifications']['total'] == 2
                    assert suite.state['summary']['tests']['fail'] == 1
                    assert suite.state['summary']['tests']['pass'] == 0

                else:
                    assert suite.state['summary']['verifications']['total'] == 1
                    assert suite.state['summary']['tests']['fail'] == 0
                    assert suite.state['summary']['tests']['pass'] == 1

            else:
        
                if fail_rqmt:
                    assert suite.state['result'] == 'FAILED'
                    assert suite.state['summary']['verifications']['total'] == 2
                    assert suite.state['summary']['tests']['fail'] == 1
                    assert suite.state['summary']['tests']['pass'] == 0

                else:
                    assert suite.state['result'] == 'PASSED'
                    assert suite.state['summary']['verifications']['total'] == 1
                    assert suite.state['summary']['tests']['fail'] == 0
                    assert suite.state['summary']['tests']['pass'] == 1



def simple():

    with TestSuite("bvt simple") as suite:
        suite.create_reports=False
        with TestCase(suite,"test1") as test:
            test.stop()
        with TestCase(suite,"test2") as test:
            test.stop(force_fail=False)
        with TestCase(suite,"test3") as test:
            with TestStep(test,"step1") as step:
                rqmts._force_pass(step)
                step.stop(force_fail=False)
        with TestCase(suite,"test4") as test:
            with TestStep(test,"step1") as step:
                rqmts._force_pass(step)
                step.stop()

    assert suite.state['summary']['tests']['total'] == 4
    assert suite.state['summary']['tests']['fail'] == 2
    assert suite.state['summary']['tests']['pass'] == 2
    assert suite.state['summary']['verifications']['total'] == 2

verify_stop_on_fail()
verify_step_stop()
verify_test_stop()
verify_suite_stop()
simple()

