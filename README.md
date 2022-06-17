# Second-level provenance information based on W3C PROV specifications

## Overview

The [**W3C PROV**](https://www.w3.org/TR/prov-overview/) standard provides a recommended family of specifications for tracking processes and responsibilities as well as describing provenance structures within complex experiments and large workflows on scientific data.

In the climate domain, provenance tracking can be addressed at two different levels. 

- The **first level** refers to the whole end-to-end scientific workflow including a proper reference to input and output datasets via PIDs. 
- The **second leve**l provides a focus on some first-level tasks, like those regarding data analytics, which can be represented themselves as a workflow of micro-tasks (analytics operators) that may usually be in the order of hundreds or thousands. 

The main idea is to navigate the first level provenance to have a complete understanding of the overall high-level end-to-end workflow and then have the opportunity to drill-down into some specific analytics tasks to get more detailed information about their internal workflow in terms of micro-tasks or analytics operators.

## Typical scenario

Scientific users can exploit the Ophidia framework and integrate an Ophidia-based analysis into a more articulated data analytics workflow. Then, based on the information about the executed analytics operators that are tracked by the Ophidia analytics engine, they can get fine-grained (second-level) provenance information, represented according to the W3C PROV specifications.

## How to use the application

The Python script allows users to retrieve the provenance documents related to a specific Ophidia analytics workflow in several formats, such as XML, JSON, RDF or graphical format. It exploits the [PROV](https://prov.readthedocs.io/en/latest/readme.html) Python library, an implementation of the W3C PROV Data Model supporting PROV-O (RDF), PROV-XML, PROV-JSON import/export.  

```
python W3C-PROV_second-level.py --input <folder containing Ophidia logs> --output <output folder>
```
