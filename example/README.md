# Second-level provenance information captured for the Tropical Nights workflow

The **Tropical Nights** climate index represents the number of days where the daily minimum temperature 𝑇𝑁 is above a reference temperature, e.g. 20°C.
The computation of the index is a workflow of several micro-tasks (analytics operators):
- Import the input NetCDF data set (minimum temperature in °K)
- Identify the tropical nights:  {𝑑𝑎𝑦∣𝑇𝑁(𝑑𝑎𝑦)>293.15}
- Count the number of yearly tropical nights
- Export the result

Users can run the **Tropical Nights Climate Index.ipynb** notebook in a Jupyter-based computing environment including an instance of the Ophidia framework; then, they can run the Python script using the Ophidia logs made available on the client side to get a provenance tracking at a finer granularity.

```
python W3C-PROV_second-level.py --input Ophidia_logs --output W3C-PROV_second-level_Output
```

![alt text](https://github.com/OphidiaBigData/ophidia-provenance/blob/main/example/W3C-PROV_second-level_Output/W3C-PROV_second-level.png?raw=true)
