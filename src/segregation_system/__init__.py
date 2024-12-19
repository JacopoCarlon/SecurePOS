import sys
from segregation_system.SegregationSystemOrchestrator import SegregationSystemOrchestrator

def main():
    controller = SegregationSystemOrchestrator()
    controller.run(False)
    sys.exit(0)

if __name__ == "__main__":
    main()
