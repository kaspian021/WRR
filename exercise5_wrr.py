from dataclasses import dataclass, field
from pathlib import Path
from threading import BoundedSemaphore, Condition
import argparse
@dataclass
class Task:
    name: str
    weight: int
    bursts: int
    remaining: int = field(init=False)
    first_start: int|None = None
    completion: int|None = None
    def __post_init__(self):
        if self.weight <= 0 or self.bursts < 0: raise ValueError("weight must be positive and bursts non-negative")
        self.remaining = self.bursts
class Guard:
    def __init__(self, mode):
        if mode not in ("semaphore","monitor","both"): raise ValueError("invalid mode")
        self.sem = BoundedSemaphore(1) if mode in ("semaphore","both") else None
        self.cv = Condition() if mode in ("monitor","both") else None
    def __enter__(self):
        if self.sem: self.sem.acquire()
        if self.cv:
            self.cv.acquire()
            while getattr(self,"busy",False): self.cv.wait()
            self.busy=True
        return self
    def __exit__(self,*_):
        if self.cv:
            self.busy=False; self.cv.notify_all(); self.cv.release()
        if self.sem: self.sem.release()
def schedule(tasks, quantum=1, mode="semaphore"):
    if quantum<=0: raise ValueError("quantum must be positive")
    tasks=list(tasks)
    if len({t.name for t in tasks})!=len(tasks): raise ValueError("task names must be unique")
    guard=Guard(mode); events=[]; gantt=[]; clock=0
    while any(t.remaining for t in tasks):
        progressed=False
        for t in tasks:
            for _ in range(t.weight):
                if not t.remaining: break
                with guard:
                    progressed=True
                    if t.first_start is None: t.first_start=clock
                    start=clock; run=min(quantum,t.remaining); t.remaining-=run; clock+=run
                    if not t.remaining: t.completion=clock
                    gantt.append({"task":t.name,"start":start,"end":clock})
                    events.append({"task":t.name,"start":start,"duration":run,"remaining":t.remaining,"mode":mode})
        if not progressed: break
    metrics={t.name:{"weight":t.weight,"burst":t.bursts,"completion":t.completion or 0,
                     "turnaround":t.completion or 0,"waiting":(t.completion or 0)-t.bursts} for t in tasks}
    return {"mode":mode,"events":events,"gantt":gantt,"metrics":metrics,"makespan":clock}
def gantt_svg(r,path):
    names=list(dict.fromkeys(x["task"] for x in r["gantt"])); scale=700/max(1,r["makespan"]); colors=["#4e79a7","#f28e2b","#59a14f"]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{100+len(names)*55}">', '<rect width="100%" height="100%" fill="white"/>',f'<text x="20" y="25">WRR Gantt — {r["mode"]}</text>']
    for i,n in enumerate(names):
        y=50+i*55; out.append(f'<text x="15" y="{y+20}">{n}</text>')
        for s in [x for x in r["gantt"] if x["task"]==n]:
            x=90+s["start"]*scale; w=(s["end"]-s["start"])*scale
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="{colors[i%3]}"/><text x="{x+w/2}" y="{y+20}" fill="white" text-anchor="middle">{n}</text>')
    out.append('</svg>'); Path(path).write_text("\n".join(out))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--mode",choices=["semaphore","monitor","both","all"],default="all"); p.add_argument("--quantum",type=int,default=1); p.add_argument("--gantt",default="wrr-gantt"); a=p.parse_args()
    for m in (["semaphore","monitor","both"] if a.mode=="all" else [a.mode]):
        r=schedule([Task("P1",3,5),Task("P2",2,4),Task("P3",1,3)],a.quantum,m); print(m,r["metrics"]); gantt_svg(r,f"{a.gantt}-{m}.svg")
if __name__=="__main__": main()
