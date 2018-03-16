import { scansTypes } from '../constants';
import scansService from '../../services/scansService';

const addScan = data => dispatch => {
  return dispatch({
    type: scansTypes.ADD_SCAN,
    payload: scansService.addScan(data)
  });
};

const getScan = id => dispatch => {
  return dispatch({
    type: scansTypes.GET_SCAN,
    payload: scansService.getScan(id)
  });
};

const getScans = (query = {}) => dispatch => {
  return dispatch({
    type: scansTypes.GET_SCANS,
    payload: scansService.getScans('', query)
  });
};

const updateScan = (id, data) => dispatch => {
  return dispatch({
    type: scansTypes.UPDATE_SCAN,
    payload: scansService.updateScan(id, data)
  });
};

const updatePartialScan = (id, data) => dispatch => {
  return dispatch({
    type: scansTypes.UPDATE_SCAN,
    payload: scansService.updatePartialScan(id, data)
  });
};

const deleteScan = id => dispatch => {
  return dispatch({
    type: scansTypes.DELETE_SCAN,
    payload: scansService.deleteScan(id)
  });
};

const startScan = id => dispatch => {
  return dispatch({
    type: scansTypes.START_SCAN,
    payload: scansService.startScan(id)
  });
};

const getScanJobs = (id, query = {}) => dispatch => {
  return dispatch({
    type: scansTypes.GET_SCAN_JOBS,
    payload: scansService.getScanJobs(id, query)
  });
};

const getScanJob = id => dispatch => {
  return dispatch({
    type: scansTypes.GET_SCAN_JOB,
    payload: scansService.getScanJob(id)
  });
};

const getScanResults = id => dispatch => {
  return dispatch({
    type: scansTypes.GET_SCAN_RESULTS,
    payload: scansService.getScanResults(id)
  });
};

const pauseScan = id => dispatch => {
  return dispatch({
    type: scansTypes.PAUSE_SCAN,
    payload: scansService.pauseScan(id)
  });
};

const cancelScan = id => dispatch => {
  return dispatch({
    type: scansTypes.CANCEL_SCAN,
    payload: scansService.cancelScan(id)
  });
};

const restartScan = id => dispatch => {
  return dispatch({
    type: scansTypes.RESTART_SCAN,
    payload: scansService.restartScan(id)
  });
};

const mergeScans = data => dispatch => {
  return dispatch({
    type: scansTypes.GET_MERGE_SCAN_RESULTS,
    payload: scansService.mergeScans(data)
  });
};

export {
  addScan,
  getScan,
  getScans,
  updateScan,
  updatePartialScan,
  deleteScan,
  startScan,
  getScanJobs,
  getScanJob,
  getScanResults,
  pauseScan,
  cancelScan,
  restartScan,
  mergeScans
};
