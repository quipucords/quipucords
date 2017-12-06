
import { combineReducers } from 'redux';
import navigationBarReducer from './navigationBarReducer';

const appReducer = combineReducers({
  navigationBar: navigationBarReducer
});

export default appReducer;
