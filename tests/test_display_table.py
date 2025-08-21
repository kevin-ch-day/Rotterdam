from utils.display_utils.table import print_table


def test_table_ascii_snapshot(capsys):
    rows = [[1, "alpha"], [2, "beta"]]
    print_table(rows, headers=["id", "name"], max_width=40)
    out = capsys.readouterr().out.strip().splitlines()
    out = "\n".join(line.rstrip() for line in out)
    assert out == "id | name\n----------\n1  | alpha\n2  | beta"
