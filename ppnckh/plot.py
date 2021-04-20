steps = [0, 2000, 4000, 6000, 8000, 10000]
losses = [100, 2.2, 1.64, 1.35, 1.14, 0.98]
accuracies = [0, 0.38, 0.52, 0.61, 0.67, 0.71]

import matplotlib.pyplot as plt

plt.plot(losses, steps)
plt.show()

plt.plot(accuracies, steps)
plt.show()