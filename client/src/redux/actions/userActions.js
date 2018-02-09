import { userTypes } from '../constants';
import userService from '../../services/userService';

const getUser = () => dispatch => {
  return dispatch({
    type: userTypes.USER_INFO,
    payload: userService.whoami()
  });
};

const authorizeUser = () => dispatch => {
  return dispatch({
    type: userTypes.USER_AUTH,
    payload: userService.authorizeUser()
  });
};

const logoutUser = () => dispatch => {
  return dispatch({
    type: userTypes.USER_LOGOUT,
    payload: userService.logoutUser()
  });
};

export { getUser, authorizeUser, logoutUser };
