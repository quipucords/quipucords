import { scansTypes } from '../constants';
import scansService from '../../services/scansService';

const addScan = data => dispatch => {
  return dispatch({
    type: scansTypes.ADD_SCAN,
    payload: scansService.addScan(data)
  });
};

const cancelScan = id => dispatch => {
  return dispatch({
    type: scansTypes.CANCEL_SCAN,
    payload: scansService.cancelScan(id)
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

const restartScan = id => dispatch => {
  return dispatch({
    type: scansTypes.RESTART_SCAN,
    payload: scansService.restartScan(id)
  });
};

export {
  addScan,
  cancelScan,
  getScan,
  getScans,
  getScanResults,
  pauseScan,
  restartScan
};
