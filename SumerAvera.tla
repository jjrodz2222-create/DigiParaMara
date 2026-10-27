---------------- MODULE SumerAvera ------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Nodes, MaxSteps

VARIABLES state, step

vars == <<state, step>>

Init == 
    /\ state = "Init"
    /\ step = 0
Next ==
    \/ /\ step < MaxSteps
       /\ \/ /\ state = "Init" 
             /\ state' = "Validated" 
             /\ step' = step + 1
          \/ /\ state = "Validated" 
             /\ state' = "InvariantLocked" 
             /\ step' = step + 1
          \/ /\ state = "InvariantLocked" 
             /\ state' = "Committed" 
             /\ step' = step + 1
          \/ /\ state = "Committed" 
             /\ state' = "Committed" 
             /\ step' = step + 1
    \/ /\ step >= MaxSteps
       /\ state' = state
       /\ step' = step

Spec == Init /\ [][Next]_vars

================================================
