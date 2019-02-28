import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import store from './store';
import reduxActions from './actions';
import reduxReducers from './reducers';
import reduxSelectors from './selectors';
import reduxTypes from './constants';

const connectRouter = (mapStateToProps, mapDispatchToProps) => component =>
  withRouter(
    connect(
      mapStateToProps,
      mapDispatchToProps
    )(component)
  );

export { connect, connectRouter, reduxActions, reduxReducers, reduxSelectors, reduxTypes, store };
