import { sourcesTypes } from '../constants';
import sourcesService from '../../services/sourcesService';

const addSource = (data, query = {}) => dispatch => {
  debugger;
  return dispatch({
    type: sourcesTypes.ADD_SOURCE,
    payload: sourcesService.addSource(data, query)
  });
};

const deleteSource = id => dispatch => {
  return dispatch({
    type: sourcesTypes.DELETE_SOURCE,
    payload: sourcesService.deleteSource(id)
  });
};

const deleteSources = (ids = []) => dispatch => {
  return dispatch({
    type: sourcesTypes.DELETE_SOURCES,
    payload: sourcesService.deleteSources(ids)
  });
};

const getSource = id => dispatch => {
  return dispatch({
    type: sourcesTypes.GET_SOURCE,
    payload: sourcesService.getSource(id)
  });
};

const getSources = (query = {}) => dispatch => {
  return dispatch({
    type: sourcesTypes.GET_SOURCES,
    payload: sourcesService.getSources('', query)
  });
};

const updateSource = (id, data) => dispatch => {
  return dispatch({
    type: sourcesTypes.UPDATE_SOURCE,
    payload: sourcesService.updateSource(id, data)
  });
};

export { addSource, deleteSource, deleteSources, getSource, getSources, updateSource };
