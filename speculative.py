import sys
import argparse
from util import ReservationStation
from util import Instruction
from util import ROBuffer


class Tomasulo:
    instructionCount = 0
    instructionList = []
    reservationStations = {}
    cycles = 0
    instCounter = 0
    issuedInstructions = 0
    maxIterations = 4
    mIssue = 1

    def __init__(self, n, addrs, multrs, brs, lrs, srs, b):
        self.mIssue = n
        self.noOfAddRS = addrs
        self.noOfMultRS = multrs
        self.noOfBranchRS = brs
        self.noOfLoadRS = lrs
        self.noOfStoreRS = srs
        self.branchPredictor = b
        self.clearList = []
        self.ROBList = []

    def initializeRS(self):
        '''
        Initializes the Reservation Station
        '''
        self.reservationStations = {
            "ADD": [],
            "MULT": [],
            "LW": [],
            "SW": [],
            "BNE": [],
        }
        for i in range(self.noOfAddRS):
            rs = ReservationStation(False, "ADD", i)
            self.reservationStations["ADD"].append(rs)

        for i in range(self.noOfMultRS):
            rs = ReservationStation(False, "MULT", i)
            self.reservationStations["MULT"].append(rs)

        for i in range(self.noOfBranchRS):
            rs = ReservationStation(False, "BNE", i)
            self.reservationStations["BNE"].append(rs)

        for i in range(self.noOfLoadRS):
            rs = ReservationStation(False, "LW", i)
            self.reservationStations["LW"].append(rs)

        for i in range(self.noOfStoreRS):
            rs = ReservationStation(False, "SW", i)
            self.reservationStations["SW"].append(rs)

    def clearRS(self, rsIndex, rsType):
        self.reservationStations[rsType].pop(rsIndex)
        rs = ReservationStation(False, rsType, i)
        self.reservationStations[rsType].append(rs)

    def has_dependency(self, source):
        '''
        check if the instruction is dependent on  previous instruction
        '''
        i = self.instCounter - 1
        while i >= 0:
            # checking if the dependent instruction is completed
            if self.instructionList[i].isDone == False:
                # check if the source is the dest of previous instruction
                if self.instructionList[i].dest == source:
                    return i
            i -= 1
        return None

    def issue(self):
        for issueIndex in range(self.mIssue):
            # if all the instructions are issued do nothing
            if self.instCounter == self.instructionCount:
                return
            curInst = self.instructionList[self.instCounter]

            rsStation = None
            if curInst.type == "ADD" or curInst.type == "SUB":
                rsStation = self.reservationStations["ADD"]
            elif curInst.type == "MULT" or curInst.type == "DIV":
                rsStation = self.reservationStations["MULT"]
            elif curInst.type == "LW":
                rsStation = self.reservationStations["LW"]
            elif curInst.type == "SW":
                rsStation = self.reservationStations["SW"]
            elif curInst.type == "BNE":
                rsStation = self.reservationStations["BNE"]

            # Find the empty slot in reservation station
            freeStation = -1
            for i in range(len(rsStation)):
                if rsStation[i].busy == False:
                    freeStation = i
                    break

            # If the reservation station is not free, do nothing
            if freeStation == -1:
                return

            # add the instruction to the free station
            rs = rsStation[freeStation]
            rs.stage = "ISSUE"
            rs.busy = True
            rs.qj = self.has_dependency(curInst.source1)
            if curInst.source2 is not None:
                rs.qk = self.has_dependency(curInst.source2)
            curInst.issueCycle = self.cycles
            rs.instIndex = self.instCounter
            rs.instruction = curInst
            # add the instruction to the Reorder buffer
            self.ROBList.append(ROBuffer(rs.instIndex))
            rs.readyForExec = self.cycles + 1
            self.instCounter += 1
            self.issuedInstructions += 1
            #print(rs.instruction.instruction, rs.qj, rs.qk)

            if curInst.type == "SW":
                rs.stage = "MEM"
                rs.readyForWb = self.cycles + 1
            elif curInst.type == "BNE":
                break

    def executeInstruction(self, rsIndex, rsStation, rsType):
        '''
        Executes the instruction
        '''
        rsStation.isExecuting = True
        # decrement the instruction timer
        rsStation.timer -= 1
        if rsStation.timer == 0:
            rsStation.readyForExec = -1
            #print("end executing", rsStation.instruction.instruction)
            self.instructionList[rsStation.instIndex].execCycle = self.cycles
            if rsType == "ADD" or rsType == "MULT":
                # add, mult, div, sub are ready for WB after execution
                rsStation.stage = "MEM"
                rsStation.readyForWb = self.cycles + 1
            elif rsType == "LW":
                # lw is ready for memory after execution
                rsStation.readyForMem = self.cycles + 1
            elif rsType == "BNE":
                # branch is ready to commit after execution
                rsStation.stage = "WB"
                self.instructionList[rsStation.instIndex].isDone = True
                # clear dependencies and update ROB
                self.update_RS(rsStation.instIndex, self.cycles)
                self.updateROB(rsType, rsStation.instIndex)
                self.clearList.append({"rsIndex": rsIndex, "rsType": rsType})

    def updateExecStage(self, rsType, rsCount):
        rsStation = self.reservationStations[rsType]
        # check if an instruction is already executing in RS
        isExecuting = False
        for i in range(rsCount):
            if (
                rsStation[i].busy == True
                and rsStation[i].qj == None
                and rsStation[i].qk == None
                and rsStation[i].isExecuting == True
                and rsStation[i].timer != 0
                and rsStation[i].readyForExec != -1
            ):
                isExecuting = True
                self.executeInstruction(i, rsStation[i], rsType)
                break

        # Otherwise execute an instruction if the dependencies are resolved
        if isExecuting == False:
            for i in range(rsCount):
                if rsStation[i].stage == "ISSUE" and rsStation[i].busy == True and rsStation[i].qj == None and rsStation[i].qk == None:
                    if rsStation[i].readyForExec != -1 and self.cycles >= rsStation[i].readyForExec:
                        # start the instruction timer
                        rsStation[i].readyForExec = self.cycles
                        rsStation[i].stage = "EXEC"
                        rsStation[i].timer = rsStation[i].instruction.cycleTime
                        self.executeInstruction(i, rsStation[i], rsType)
                        break

    def updateMemStage(self, rsType, rsCount):
        rsStation = self.reservationStations[rsType]
        for i in range(rsCount):
            if rsStation[i].stage == "EXEC" and rsStation[i].busy == True and rsStation[i].qj == None and rsStation[i].qk == None:
                if self.cycles >= rsStation[i].readyForMem and rsStation[i].readyForMem != -1:
                    rsStation[i].isExecuting = False
                    rsStation[i].stage = "MEM"
                    rsStation[i].readyForMem = -1
                    rsStation[i].readyForWb = self.cycles + 1
                    self.instructionList[rsStation[i].instIndex].memCycle = self.cycles

    def updateWbStage(self, rsType, rsCount):
        rsStation = self.reservationStations[rsType]
        for i in range(rsCount):
            if rsStation[i].stage == "MEM" and rsStation[i].busy == True and rsStation[i].qj == None and rsStation[i].qk == None:
                if (
                    self.cycles >= rsStation[i].readyForWb
                    and rsStation[i].readyForWb != -1
                ):
                    rsStation[i].isExecuting = False
                    rsStation[i].readyForWb = -1
                    rsStation[i].stage = "WB"
                    self.instructionList[rsStation[i].instIndex].isDone = True
                    # update the instructions in RS that are dependent on this instruction
                    if rsType != "SW":
                        self.instructionList[rsStation[i]
                                             .instIndex].wbCycle = self.cycles
                    self.update_RS(rsStation[i].instIndex, self.cycles)
                    self.updateROB(rsType, rsStation[i].instIndex)
                    self.clearList.append({"rsIndex": i, "rsType": rsType})

    def commit(self):
        for i in range(len(self.ROBList)):
            robEntry = self.ROBList[i]
            # If the instruction in ROB is ready, commit in the next cycle
            if robEntry.ready == False:
                break

            elif robEntry.ready == True and robEntry.isCommited == False:
                if self.cycles > robEntry.readyCycle:
                    robEntry.isCommited = True
                    self.instructionList[robEntry.instIndex].commitCycle = self.cycles
                    if self.ROBList[i].type == "BNE" and self.branchPredictor == "NT":
                        # if the branch is not taken flush the instructions after branch
                        self.flush()
                    break
                else:
                    break

    def flush(self):
        # prevents next issue
        self.instCounter = self.instructionCount
        for i in range(self.noOfAddRS):
            self.reservationStations["ADD"][i].busy = False

        for i in range(self.noOfMultRS):
            self.reservationStations["MULT"][i].busy = False

        for i in range(self.noOfBranchRS):
            self.reservationStations["BNE"][i].busy = False

        for i in range(self.noOfLoadRS):
            self.reservationStations["LW"][i].busy = False

        for i in range(self.noOfStoreRS):
            self.reservationStations["SW"][i].busy = False

    def updateROB(self, rsType, instIndex):
        for i in range(len(self.ROBList)):
            ROBEntry = self.ROBList[i]
            if ROBEntry.instIndex == instIndex:
                ROBEntry.type = rsType
                ROBEntry.ready = True
                ROBEntry.readyCycle = self.cycles

    def update_RS(self, instIndex, cycles):
        for i in range(self.noOfAddRS):
            rs_station = self.reservationStations["ADD"][i]
            if rs_station.busy == True:
                if rs_station.qj == instIndex:
                    rs_station.qj = None
                if rs_station.qk == instIndex:
                    rs_station.qk = None

        for i in range(self.noOfMultRS):
            rs_station = self.reservationStations["MULT"][i]
            if rs_station.busy == True:
                if rs_station.qj == instIndex:
                    rs_station.qj = None
                if rs_station.qk == instIndex:
                    rs_station.qk = None

        for i in range(self.noOfBranchRS):
            rs_station = self.reservationStations["BNE"][i]
            if rs_station.busy == True:
                if rs_station.qj == instIndex:
                    rs_station.qj = None
                if rs_station.qk == instIndex:
                    rs_station.qk = None

        for i in range(self.noOfLoadRS):
            rs_station = self.reservationStations["LW"][i]
            if rs_station.busy == True:
                if rs_station.qj == instIndex:
                    rs_station.qj = None
                if rs_station.qk == instIndex:
                    rs_station.qk = None

        for i in range(self.noOfStoreRS):
            rs_station = self.reservationStations["SW"][i]
            if rs_station.busy == True:
                if rs_station.qj == instIndex:
                    rs_station.qj = None
                if rs_station.qk == instIndex:
                    rs_station.qk = None

    def execute(self):
        self.updateExecStage("ADD", self.noOfAddRS)
        self.updateExecStage("MULT", self.noOfMultRS)
        self.updateExecStage("LW", self.noOfLoadRS)
        self.updateExecStage("BNE", self.noOfBranchRS)

    def memory(self):
        self.updateMemStage("LW", self.noOfLoadRS)

    def writeback(self):
        self.updateWbStage("ADD", self.noOfAddRS)
        self.updateWbStage("MULT", self.noOfMultRS)
        self.updateWbStage("LW", self.noOfLoadRS)
        self.updateWbStage("SW", self.noOfStoreRS)
        # update the reservation stations
        for i in range(len(self.clearList)):
            self.clearRS(self.clearList[i]["rsIndex"],
                         self.clearList[i]["rsType"])
        self.clearList = []

    def done(self):
        if self.instCounter != self.instructionCount:
            return False
        else:
            for i in range(self.noOfAddRS):
                if self.reservationStations["ADD"][i].busy == True:
                    return False
            for i in range(self.noOfMultRS):
                if self.reservationStations["MULT"][i].busy == True:
                    return False
            for i in range(self.noOfBranchRS):
                if self.reservationStations["BNE"][i].busy == True:
                    return False
            for i in range(self.noOfLoadRS):
                if self.reservationStations["LW"][i].busy == True:
                    return False
            for i in range(self.noOfStoreRS):
                if self.reservationStations["SW"][i].busy == True:
                    return False
            if self.branchPredictor == "T":
                # if the branch is predicted taken, check if all the instrutions are commited
                for i in range(len(self.instructionList)):
                    if self.instructionList[i].commitCycle == "-":
                        return False
            return True

    def print_result(self):
        counter = 0
        if self.issuedInstructions < self.instructionCount:
            counter = self.issuedInstructions
        else:
            counter = self.instructionCount
        print("Iteration\tInstruction\t\tIssue\tExec\tMem\tWriteCDB\tCommit")
        for i in range(counter):
            inst = self.instructionList[i]
            print(
                f"{inst.iteration}\t\t{inst.instruction}\t\t{inst.issueCycle}\t{inst.execCycle}\t{inst.memCycle}\t{inst.wbCycle}\t\t{inst.commitCycle}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tomasulo Simulator", allow_abbrev=False
    )
    parser.add_argument(
        "-n", type=int, help="No of instructions to issue", default=2
    )
    parser.add_argument("-acycles", type=int,
                        help="Addr Cycles", default=1)
    parser.add_argument("-mcycles", type=int,
                        help="Mult/Div Cycles", default=1)
    parser.add_argument("-bcycles", type=int,
                        help="Branch Cycles", default=1)
    parser.add_argument("-lcycles", type=int,
                        help="Load Cycles", default=1)
    parser.add_argument(
        "-addrs", type=int, help="No of Adder Reservation stations", default=3
    )
    parser.add_argument(
        "-multrs", type=int, help="No of Mult Reservation stations", default=3
    )
    parser.add_argument(
        "-brs", type=int, help="No of Branch Reservation stations", default=3
    )
    parser.add_argument(
        "-lrs", type=int, help="No of Load Buffer entries", default=3)
    parser.add_argument(
        "-srs", type=int, help="No of Store Buffer entries", default=3)
    parser.add_argument(
        "-b",
        type=str,
        help="Static Branch Predictor",
        choices=["T", "NT"],
        default="T",
    )
    parser.add_argument("-f", help="input file name", required=True)
    args = parser.parse_args()
    filename = args.f
    tempList = []
    tomasulo = Tomasulo(
        args.n,
        args.addrs,
        args.multrs,
        args.brs,
        args.lrs,
        args.srs,
        args.b,
    )
    instCycles = {
        "addCycles": args.acycles,
        "multCycles": args.mcycles,
        "branchCycles": args.bcycles,
        "loadCycles": args.lcycles
    }
    try:
        with open(filename, "r") as reader:
            print("Reading input file " + filename)
            for line in reader.readlines():
                if line.strip():
                    tempList.append(line.strip())
    except:
        print("Error reading ", filename)

    tomasulo.maxIterations = 4

    for i in range(tomasulo.maxIterations):
        for j in range(len(tempList)):
            instruction = tempList[j]
            tomasulo.instructionList.append(
                Instruction(tomasulo.instructionCount,
                            i, instruction, instCycles)
            )
            tomasulo.instructionCount += 1

    tomasulo.initializeRS()
    while tomasulo.done() == False:
        tomasulo.cycles += 1
        tomasulo.issue()
        tomasulo.execute()
        tomasulo.memory()
        tomasulo.writeback()
        tomasulo.commit()

    # printing the result
    tomasulo.print_result()
