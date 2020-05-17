class Instruction:
    source1 = None
    source2 = None
    dest = None
    issueCycle = "-"
    execCycle = "-"
    memCycle = "-"
    wbCycle = "-"
    commitCycle = "-"
    iteration = 0
    instNumber = 0
    cycleTime = 0
    isDone = False

    def __init__(self, index, iteration, inst, cycles):
        self.instruction = inst
        self.instNumber = index
        self.iteration = iteration
        self.cycleTime = 0
        tokens = inst.split(" ")
        self.type = tokens[0]
        if len(tokens) > 1:
            self.dest = tokens[1]
        if len(tokens) > 2:
            self.source1 = tokens[2]
        if len(tokens) > 3:
            self.source2 = tokens[3]

        # SW and BNE has 2 source operands and no destination operand
        if self.type == "SW" or self.type == "BNE":
            if self.type == "BNE":
                self.cycleTime = cycles['branchCycles']
            self.source2 = self.source1
            self.source1 = self.dest
            self.dest = None
        elif self.type == "ADD" or self.type == "SUB":
            self.cycleTime = cycles['addCycles']
        elif self.type == "MULT" or self.type == "DIV":
            self.cycleTime = cycles['multCycles']
        elif self.type == "LW":
            self.cycleTime = cycles['loadCycles']


class ROBuffer:
    ready = False

    def __init__(self, index):
        self.instIndex = index
        self.readyCycle = -1
        self.isCommited = False


class ReservationStation:
    instIndex = None
    instruction = None
    timer = -1
    qj = None
    qk = None
    stage = None
    readyForExec = -1
    readyForMem = -1
    readyForWb = -1
    readyForCommit = -1
    isExecuting = False

    def __init__(self, busy, type, i):
        self.busy = busy
        self.type = type
        self.index = i

    def clear(self):
        self.instIndex = None
        self.instruction = None
        self.timer = -1
        self.busy = False
        self.qj = None
        self.qk = None
        self.readyForExec = -1
        self.readyForMem = -1
        self.readyForWb = -1
        self.readyForCommit = -1
        self.isExecuting = False
