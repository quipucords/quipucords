import { scansTypes } from '../constants';
import scansService from '../../services/scansService';

const dispatchObjects = {
  addScan: data => {
    return {
      type: scansTypes.ADD_SCAN,
      payload: scansService.addScan(data)
    };
  },
  cancelScan: id => {
    return {
      type: scansTypes.CANCEL_SCAN,
      payload: scansService.cancelScan(id)
    };
  },
  getScan: id => {
    return {
      type: scansTypes.GET_SCAN,
      payload: scansService.getScan(id)
    };
  },
  getScans: (query = {}) => {
    return {
      type: scansTypes.GET_SCANS,
      payload: scansService.getScans('', query)
    };
  },
  getScanResults: id => {
    return {
      type: scansTypes.GET_SCAN_RESULTS,
      payload: scansService.getScanResults(id)
    };
  },
  pauseScan: id => {
    return {
      type: scansTypes.PAUSE_SCAN,
      payload: scansService.pauseScan(id)
    };
  },
  restartScan: id => {
    return {
      type: scansTypes.RESTART_SCAN,
      payload: scansService.restartScan(id)
    };
  }
};

const addScan = data => dispatch => {
  return dispatch(dispatchObjects.addScan(data));
};

const cancelScan = id => dispatch => {
  return dispatch(dispatchObjects.cancelScan(id));
};

const getScan = id => dispatch => {
  return dispatch(dispatchObjects.getScan(id));
};

const getScans = (query = {}) => dispatch => {
  return dispatch(dispatchObjects.getScans(query));
};

const getScanResults = id => dispatch => {
  return dispatch(dispatchObjects.getScanResults(id));
};

const pauseScan = id => dispatch => {
  return dispatch(dispatchObjects.pauseScan(id));
};

const restartScan = id => dispatch => {
  return dispatch(dispatchObjects.restartScan(id));
};

export { dispatchObjects, addScan, cancelScan, getScan, getScans, getScanResults, pauseScan, restartScan };
