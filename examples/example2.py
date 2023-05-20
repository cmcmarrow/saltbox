from saltbox import saltbox
from saltbox.orchestration import Orchestration


with Orchestration([(1, saltbox.SaltBoxBuilder("docker",
                                               "build",
                                               master_build=True,
                                               salt="3005")),
                    (2, saltbox.SaltBoxBuilder("docker",
                                               "minion",
                                               minion_build=True))]) as d:

    print(d["build_master"].run("salt '*' test.ping").output)
