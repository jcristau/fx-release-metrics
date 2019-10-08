FROM python
COPY script.py .
RUN pip install requests
CMD python3 ./script.py
