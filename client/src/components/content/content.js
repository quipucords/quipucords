import React, { Component } from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { connect } from 'react-redux';
import ClassNames from 'classnames';

import Sources from '../sources/sources';
import Scans from '../scans/scans';

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
          <Redirect from="/" to="/sources"/>
        </Switch>
      </div>
    );
  }
}

function mapStateToProps(state, ownProps) {
  return state;
}

export default connect(mapStateToProps)(
  Content
);
