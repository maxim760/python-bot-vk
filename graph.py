import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from math import ceil
import numpy as np
from utils import get_random_id, with_spaces, no_fractions

def get_image_graph(dates, died, save, active):
  died = np.array(died)
  save = np.array(save)
  active = np.array(active)
  
  x = [datetime.strptime(d,'%d.%m.%Y').date() for d in dates]
  fig= plt.figure(figsize=(8,4.5))
  ax = fig.add_subplot(111)
  plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%#d.%m"))
  ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x,p: no_fractions(with_spaces(x))))
  
  line_active, color_active = active, "#FBDF4D"
  line_save, color_save = active + save, "#4CA64C"
  line_died, color_died = active + save + died, "#FF0000"
  plt.plot(x, line_active, label="Активных", color=color_active, linewidth=2)
  plt.plot(x, line_save, label="Вылечено", color=color_save, linewidth=2)
  plt.plot(x, line_died, label="Умерло", color=color_died, linewidth=2)
  ax.fill_between(x, 0, line_active, color=color_active, alpha=0.85)
  ax.fill_between(x, line_active, line_save, color=color_save, alpha=0.85)
  ax.fill_between(x, line_save, line_died, color=color_died, alpha=0.85)
  ax.xaxis_date()
  fig.autofmt_xdate()
  plt.grid(axis="y")
  ax.set_ylim(ymin=0)
  plt.yticks(np.arange(0, int(ceil(max(active+save+died) / 10 ** 6) * 10 ** 6) + 1, 0.5 * 10 ** 6))
  plt.margins(x=0,y=0)
  ax.legend(loc="best", framealpha=0.9)
  ax.tick_params(axis="x", rotation=0)
  for tick in ax.xaxis.get_major_ticks():
    tick.label1.set_horizontalalignment('center')
  name = get_random_id() + ".png"
  fig.savefig(name, dpi = 300)
  return name
