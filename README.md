# Tomasulo Simulator / Solver

## Dependencies

- Python 3

## Assumptions

- Memory takes one cycle
- Only one instruction can commit per cycle
- If taken, branch will exit after 4 iterations

## Limitations

- Supports only basic instructions ADD, MULT, SUB, DIV, LW, SW, BNE

## Steps to run

- Non-speculative Tomasulo

```sh
$ python3 main.py -f [filename] -n [n] -acycles [acycles] -mcycles [mcycles] -bcycles [bcycles] -lcycles [lcycles] -addrs [addrs] -multrs [multrs] -brs [brs] -lrs [lrs] -srs [srs] -b [b]
```

- Speculative Tomasulo

```sh
$ python3 speculative.py -f [filename] -n [n] -acycles [acycles] -mcycles [mcycles] -bcycles [bcycles] -lcycles [lcycles] -addrs [addrs] -multrs [multrs] -brs [brs] -lrs [lrs] -srs [srs] -b [b]
```

## Tomasulo Configuration

- **f** - input file name
- **n** - No of instructions to issue (default=1)
- **acycles** - Addr unit Cycles (default=1)
- **mcycles** - Mult/Div unit Cycles (default=1)
- **bcycles** - Branch Cycles (default=1)
- **lcycles** - Load Cycles (default=1)
- **addrs** - No of Adder Reservation stations (default=3)
- **multrs** - No of Mult Reservation stations (default=3)
- **brs** - No of Branch Reservation stations (default=3)
- **lrs** - No of Load Buffer entries (default=5)
- **srs** - No of Store Buffer entries (default=5)
- **b** - Static Branch Predictor (takes values "T" or "NT", default = "T")

## Example

- Non-speculative & branch taken

```sh
$ python3 main.py -f instruction.txt -n 2 -acycles 2 -mcycles 2 -bcycles 1 -lcycles 1 -addrs 3 -multrs 3 -brs 3 -lrs 5 -srs 5 -b T
```

- Non-speculative & branch not taken

```sh
$ python3 main.py -f instruction.txt -n 2 -acycles 2 -mcycles 2 -bcycles 1 -lcycles 1 -addrs 3 -multrs 3 -brs 3 -lrs 5 -srs 5 -b NT
```

- Speculative & branch taken

```sh
$ python3 speculative.py -f instruction.txt -n 2 -acycles 2 -mcycles 2 -bcycles 1 -lcycles 1 -addrs 3 -multrs 3 -brs 3 -lrs 5 -srs 5 -b T
```
