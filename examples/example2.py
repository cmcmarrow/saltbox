from saltbox import saltbox
from saltbox.orchestration import Orchestration
from saltbox import saltidle


with Orchestration([(1, saltbox.SaltBoxBuilder("docker",
                                               "build",
                                               master_build=True,
                                               minion_build=True)),
                    (2, saltbox.SaltBoxBuilder("docker",
                                               "minion",
                                               minion_build=True))]) as d:
    print(list(d))
    print(d["build_master"].run("salt '*' test.ping").output)
    print(d["minion_1"].run("salt-call --local test.ping").output)
    saltidle.run(d)
