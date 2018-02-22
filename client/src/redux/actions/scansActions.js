import { scansTypes } from '../constants';
import scansService from '../../services/scansService';

const getScan = id => dispatch => {
  return dispatch(dispatchObjects.getScan(id));
};

const getScans = (query = {}) => dispatch => {
  return dispatch(dispatchObjects.getScans(query));
};

const getScanResults = id => dispatch => {
  return dispatch(dispatchObjects.getScanResults(id));
};

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

const pauseScan = id => dispatch => {
  return dispatch(dispatchObjects.pauseScan(id));
};

const restartScan = id => dispatch => {
  return dispatch(dispatchObjects.restartScan(id));
};

export { getScan, getScans, getScanResults, addScan, cancelScan, pauseScan, restartScan };
