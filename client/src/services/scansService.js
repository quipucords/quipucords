import axios from 'axios';
import serviceConfig from './config';

const addScan = (data = {}) =>
  axios(
    serviceConfig({
      method: 'post',
      url: `${process.env.REACT_APP_SCANS_SERVICE}`,
      data
    })
  );

const getScans = (id = '', params = {}) =>
  axios(
    serviceConfig(
      {
        url: `${process.env.REACT_APP_SCANS_SERVICE}${id}`,
        params
      },
      false
    )
  );

const getScan = id => getScans(id);

const updateScan = (id, data = {}) =>
  axios(
    serviceConfig({
      method: 'put',
      url: `${process.env.REACT_APP_SCANS_SERVICE}${id}`,
      data
    })
  );

const updatePartialScan = (id, data = {}) =>
  axios(
    serviceConfig({
      method: 'patch',
      url: `${process.env.REACT_APP_SCANS_SERVICE}${id}`,
      data
    })
  );

const deleteScan = id =>
  axios(
    serviceConfig({
      method: 'delete',
      url: `${process.env.REACT_APP_SCANS_SERVICE}${id}`
    })
  );

const startScan = id =>
  axios(
    serviceConfig({
      method: 'post',
      url: process.env.REACT_APP_SCAN_JOBS_SERVICE_START_GET.replace('{0}', id)
    })
  );

const getScanJobs = (id, params = {}) =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_SCAN_JOBS_SERVICE_START_GET.replace('{0}', id),
        timeout: process.env.REACT_APP_AJAX_TIMEOUT,
        params
      },
      false
    )
  );

const getScanJob = id =>
  axios(
    serviceConfig(
      {
        url: `${process.env.REACT_APP_SCAN_JOBS_SERVICE}${id}`,
        timeout: process.env.REACT_APP_AJAX_TIMEOUT
      },
      false
    )
  );

const getConnectionScanResults = (id, params = {}) =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_SCAN_JOBS_SERVICE_CONNECTION.replace('{0}', id),
        params
      },
      false
    )
  );

const getInspectionScanResults = (id, params = {}) =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_SCAN_JOBS_SERVICE_INSPECTION.replace('{0}', id),
        params
      },
      false
    )
  );

const pauseScan = id =>
  axios(
    serviceConfig({
      method: 'put',
      url: process.env.REACT_APP_SCAN_JOBS_SERVICE_PAUSE.replace('{0}', id)
    })
  );

const cancelScan = id =>
  axios(
    serviceConfig({
      method: 'put',
      url: process.env.REACT_APP_SCAN_JOBS_SERVICE_CANCEL.replace('{0}', id)
    })
  );

const restartScan = id =>
  axios(
    serviceConfig({
      method: 'put',
      url: process.env.REACT_APP_SCAN_JOBS_SERVICE_RESTART.replace('{0}', id)
    })
  );

const scansService = {
  addScan,
  getScans,
  getScan,
  updateScan,
  updatePartialScan,
  deleteScan,
  startScan,
  getScanJobs,
  getScanJob,
  getConnectionScanResults,
  getInspectionScanResults,
  pauseScan,
  cancelScan,
  restartScan
};

export {
  scansService as default,
  scansService,
  addScan,
  getScans,
  getScan,
  updateScan,
  updatePartialScan,
  deleteScan,
  startScan,
  getScanJobs,
  getScanJob,
  getConnectionScanResults,
  getInspectionScanResults,
  pauseScan,
  cancelScan,
  restartScan
};
