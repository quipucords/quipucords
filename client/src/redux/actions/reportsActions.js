import { reportsTypes } from '../constants';
import reportsService from '../../services/reportsService';

const getReports = query => dispatch => {
  return dispatch({
    type: reportsTypes.GET_REPORTS,
    payload: reportsService.getReports(query)
  });
};

export { getReports };
