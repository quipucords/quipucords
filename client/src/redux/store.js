import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import reduxReducers from './reducers';

const hydrateStore = () => {
  // Create any initial state items based on stored data (cookies etc.)
  return {};
};

const store = createStore(
  reduxReducers,
  hydrateStore(),
  applyMiddleware(thunkMiddleware)
);

export default store;
