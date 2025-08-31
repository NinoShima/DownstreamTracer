# 🚀 FTTH DownstreamTracer

Automate downstream address selection in FTTH design — save time, improve accuracy.

# 📌 Overview

In FTTH (Fiber To The Home) network design, it's often necessary to verify connection points — for example, calculating how many users or MSTs (Multiport Service Terminals) are connected from a specific point on the cable to its end.

Manually selecting addresses multiple times with the Selection Feature tool can be time-consuming and error-prone.

# ⚡ What This Tool Does

This tool automates the selection of downstream points starting from a clicked point on the network. It helps you:

⏱ Save time — avoid repeated manual selections

🎯 Improve accuracy — quickly verify user and MST counts

🛠 Streamline workflows — make FTTH design more efficient

With this tool, FTTH designers can focus on network planning rather than repetitive selection tasks.

# 🧩 Usage

1. Load the required layers — Make sure your QGIS project has loaded the point and line layers you want to analyze.

2. Run the script — Open the QGIS Python Console and execute DownstreamTracer.py.

3. Select layers — Choose the point and line layers from the dialog.

4. Click a point to trace — Click on an interested point on the map, and the tool will automatically display the downstream results.
