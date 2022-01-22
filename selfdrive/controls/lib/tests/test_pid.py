#!/usr/bin/env python3
import random
import unittest
import sys

from common.numpy_fast import clip, interp
from common.filter_simple import FirstOrderFilter
from selfdrive.controls.lib.pid import PIController

gain_range = 10 # (1 / range -> 1 ->  range   )
ratio = 4 #   I = (P / ratio -> P -> P * ratio)

num_divs = 8# (2*n + 1)**2 graphs
_p = [[0, num_divs, 2*num_divs],[1/gain_range, 1, gain_range]]

rate_limit = 1
sec = 15

# 1 is perfect FF here

if __name__ == "__main__":
  plot_debug = False
  debug_noise = False
  debug_override = False
  debug_ramp = False
  if len(sys.argv) > 1:
    if "noise" in sys.argv:
      debug_noise = True
    if "override" in sys.argv:
      debug_override = True
    if "ramp" in sys.argv:
      debug_ramp = True
    if "plot" in sys.argv:
      plot_debug = True
    if "debug_only" in sys.argv:
      plot_all = False
    else:
      plot_all = True
    if (plot_debug and not (debug_noise or debug_override or debug_ramp)) or "debug" in sys.argv:
      debug_noise = True
      debug_override = True
      debug_ramp = True
    if (plot_debug):
      num_divs = 4 # (2*n + 1)**2 graphs (81 graphs)
      _p = [[0, num_divs, 2*num_divs],[1/gain_range, 1, gain_range]]
    #remove args so unittest is not freaked out
    while len(sys.argv) > 1:
      sys.argv.pop()
  
if plot_debug and (debug_noise or debug_override or debug_ramp):
  import matplotlib.pyplot as plt


class TestPID(unittest.TestCase):
  def test_error_noise(self):
    #TODO New Tests
    #TODO check that the average deviation from the noiseless reference is driven to 0
    #TODO check that the saturated ramp up condition(s?) are not degraded. 

    self.assertFalse((debug_ramp or debug_override) and not debug_noise, msg="Test skipped for debugging")
    for i in range(0, 2*num_divs + 1):
      for j in range (0, 2*num_divs + 1):
        kp = interp(i, _p[0], _p[1])
        _i = [[0, num_divs, 2*num_divs], [kp/ratio, kp, ratio*kp]]
        ki = interp(j, _i[0], _i[1])
        pid_n = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        pid_r = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        output_n = FirstOrderFilter(0, 1, .01)
        output_r = FirstOrderFilter(0, 1, .01)
        last_pid_n_control = 0
        last_pid_r_control = 0
        target = 0
        noise = 0
        if plot_debug and debug_noise:
          x = []
          y4 = []
          y5 = []
        for t in range(0, int(sec*100)):
          if plot_debug and debug_noise:
            x.append(t)
            y4.append(output_n.x)
            y5.append(output_r.x)
          noise = 0
          target = 0
          if (t > 10):
            target = 50

          if target != 0:
            noise = 10 * (rate_limit / kp) * ((random.randint(0, 200) - 100) / 100)

          pid_n_control_raw = pid_n.update(target+noise, output_n.x, last_output=last_pid_n_control, feedforward=target+noise)
          pid_n_control = clip(pid_n_control_raw, last_pid_n_control - rate_limit, last_pid_n_control + rate_limit)

          pid_r_control_raw = pid_r.update(target, output_r.x, last_output=last_pid_r_control, feedforward=target)
          pid_r_control = clip(pid_r_control_raw, last_pid_r_control - rate_limit, last_pid_r_control + rate_limit)
          
          last_pid_n_control = pid_n_control
          last_pid_r_control = pid_r_control
          output_n.update(pid_n_control)
          output_r.update(pid_r_control)

        if plot_debug and debug_noise and plot_all:
          plt.plot(x, y5, 'k', label="Target")
          plt.plot(x, y4, label="pid.py")
          plt.title(f"Noise Test: P = {kp:5.3}, I = {ki:5.3}")
          plt.legend()
          plt.show()
  
  def test_override(self):
    #TODO New Tests
    #TODO check that output is stable?
    #TODO check that overshoot is reduced?
    #TODO check that integrator motion is reduced / reversed during override

    self.assertFalse((debug_ramp or debug_noise) and not debug_override, msg="Test skipped for debugging")
    for i in range(0, 2*num_divs + 1):
      for j in range (0, 2*num_divs + 1):
        kp = interp(i, _p[0], _p[1])
        _i = [[0, num_divs, 2*num_divs], [kp/ratio, kp, ratio*kp]]
        ki = interp(j, _i[0], _i[1])
        pid_n = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        pid_r = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        output_n = FirstOrderFilter(0, 1, .01)
        output_r = FirstOrderFilter(0, 1, .01)
        last_pid_n_control = 0
        last_pid_r_control = 0
        target = 0
        if plot_debug and debug_override:
          x = []
          x2 = []
          y2 = []
          y4 = []
          y5 = []
        for t in range(0, int(sec*100)):
          if plot_debug and debug_override:
            x.append(t)
            x2.append(t + 500 - 10)
            y4.append(output_n.x)
            y5.append(output_r.x)
          target = 0
          if (t > 10):
            target = 50

          pid_n_control_raw = pid_n.update(target, output_n.x, last_output=last_pid_n_control)
          pid_n_control = clip(pid_n_control_raw, last_pid_n_control - rate_limit, last_pid_n_control + rate_limit)

          pid_r_control_raw = pid_r.update(target, output_r.x, last_output=last_pid_r_control)
          pid_r_control = clip(pid_r_control_raw, last_pid_r_control - rate_limit, last_pid_r_control + rate_limit)
          
          last_pid_r_control = pid_r_control
          output_r.update(pid_r_control)

                    # override / hold output of controller at 0 
          if t > 500:
            last_pid_n_control = pid_n_control
            output_n.update(pid_n_control)
          else: 
            last_pid_n_control = 0
            

        if plot_debug and debug_override and plot_all:
          plt.plot(x2, y5, 'k', label="Target")
          plt.plot(x, y2, label="Classic")
          plt.plot(x, y4, label="pid.py")
          plt.title(f"Override Test: P = {kp:5.3}, I = {ki:5.3}")
          plt.legend()
          plt.show()

  def test_ramp_up(self):
    #TODO New Tests
    #TODO check that output is stable?
    #TODO check that overshoot is reduced?
    #TODO check that integrator motion is restricted or reversed?

    self.assertFalse((debug_override or debug_noise) and not debug_ramp, msg="Test skipped for debugging")
    for i in range(0, 2*num_divs + 1):
      for j in range (0, 2*num_divs + 1):
        kp = interp(i, _p[0], _p[1])
        _i = [[0, num_divs, 2*num_divs], [kp/ratio, kp, ratio*kp]]
        ki = interp(j, _i[0], _i[1])
        pid_n = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        pid_r = PIController(([0, 1], [kp, kp]), ([0, 1], [ki, ki]), k_f=1, pos_limit=100, neg_limit=-100)
        output_n = FirstOrderFilter(0, 1, .01)
        output_r = FirstOrderFilter(0, 1, .01)
        last_pid_n_control = 0
        last_pid_r_control = 0
        target = 0
        if plot_debug and debug_ramp:
          x = []
          y4 = []
          y5 = []
        for t in range(0, int(sec*100)):
          if plot_debug and debug_ramp:
            x.append(t)
            y4.append(output_n.x)
            y5.append(output_r.x)
          target = 0
          if (t > 10):
            target = 50

          pid_n_control_raw = pid_n.update(target, output_n.x, last_output=last_pid_n_control)
          pid_n_control = clip(pid_n_control_raw, last_pid_n_control - rate_limit, last_pid_n_control + rate_limit)

          last_pid_r_control = pid_r.update(target, output_r.x, last_output=last_pid_r_control)

          last_pid_n_control = pid_n_control
          output_n.update(pid_n_control)
          output_r.update(last_pid_r_control)
            

        if plot_debug and debug_ramp and plot_all:
          plt.plot(x, y5, 'k', label="Target")
          plt.plot(x, y4, label="pid.py")
          plt.title(f"Slew Rate Limit Test: P = {kp:5.3}, I = {ki:5.3}")
          plt.legend()
          plt.show()

if __name__ == "__main__":
  unittest.main()
