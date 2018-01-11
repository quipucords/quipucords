import ClassNames from 'classnames';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withRouter } from 'react-router';

import Scans from '../scans/scans';
import Sources from '../sources/sources';

class Content extends Component {
  render() {
    let classes = ClassNames({
      'container-fluid': true,
      'container-cards-pf': true,
      'container-pf-nav-pf-vertical': true,
      'collapsed-nav': this.props.navigationBar.collapsed
    });

    return (
      <div className={classes}>
        <Switch>
          <Route path="/sources" component={Sources} />
          <Route path="/scans" component={Scans} />
          <Redirect from="/" to="/sources" />
        </Switch>
      </div>
    );
  }
}
Content.propTypes = {
  navigationBar: PropTypes.object
};

function mapStateToProps(state, ownProps) {
  return state;
}

export default withRouter(connect(mapStateToProps)(Content));
