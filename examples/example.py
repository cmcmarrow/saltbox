from saltbox.utils.file import FileBridge, FileData
from saltbox import saltbox
from saltbox.orchestration import Orchestration

APACHE = """
apache:
  service.running:
    - require:
      - pkg: apache"""

with Orchestration([(1, saltbox.SaltBoxBuilder("docker",
                                               "build",
                                               master_build=True,
                                               minion_build=True,
                                               ports={"4444", "4333"},
                                               state_files=[FileBridge(FileData("a.sls", APACHE), "a.sls")],
                                               salt="3005")),
                    (2, saltbox.SaltBoxBuilder("docker",
                                               "minion",
                                               minion_build=True,
                                               copies=[FileBridge(FileData("data.txt", "DATA MEOW"), "/data.txt")])),
                    (2, saltbox.SaltBoxBuilder("docker",
                                               "minion_old",
                                               minion_build=True,
                                               python_packages=("saltext.vmware",),
                                               salt="3004"))
                    ]) as d:
    print(list(d))
    print(d["build_master"].run("salt '*' test.ping").output)
    print(d["build_master"].run("salt '*' cmd.run 'ls /'").output)
    print(d["minion_old_1"].run("salt-call --local test.ping").output)
    print(d["build_master"].run("salt '*' state.apply a").output)
    print(d["build_master"].run("ls srv/salt").output)
