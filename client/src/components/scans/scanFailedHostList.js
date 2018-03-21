import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { EmptyState, Grid, Icon } from 'patternfly-react';
import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import { getConnectionScanResults, getInspectionScanResults } from '../../redux/actions/scansActions';

class ScanFailedHostList extends React.Component {
  constructor() {
    super();

    this.state = {
      scanResults: [],
      scanResultsError: false,
      connectionScanResultsPending: false,
      inspectionScanResultsPending: false
    };
  }

  componentDidMount() {
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh)) {
      this.refresh();
    }
  }

  isIpAddress(name) {
    let vals = name.split('.');
    if (vals.length === 4) {
      return _.find(vals, val => Number.isNaN(val)) === undefined;
    }
    return false;
  }

  ipAddressValue(name) {
    const values = name.split('.');
    return values[0] * 0x1000000 + values[1] * 0x10000 + values[2] * 0x100 + values[3] * 1;
  }

  addResults(results) {
    const { scanResults } = this.state;

    let failedResults = [];
    _.forEach(_.get(results, 'value.data.results', []), result => {
      if (result.status === 'failed') {
        failedResults.push(result);
      }
    });

    let allResults = [...scanResults, ...failedResults];

    allResults.sort((item1, item2) => {
      if (this.isIpAddress(item1.name) && this.isIpAddress(item2.name)) {
        const value1 = this.ipAddressValue(item1.name);
        const value2 = this.ipAddressValue(item2.name);

        return value1 - value2;
      }

      return item1.name.localeCompare(item2.name);
    });

    return allResults;
  }

  getInspectionResults(page) {
    const { scan, getInspectionScanResults } = this.props;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: 'failed'
    };

    getInspectionScanResults(scan.most_recent.id, queryObject)
      .then(results => {
        const morePages = _.get(results.value, 'data.next') !== null;
        this.setState({
          inspectionScanResultsPending: morePages,
          scanResults: this.addResults(results)
        });

        if (morePages) {
          this.getInspectionResults(page + 1);
        }
      })
      .catch(error => {
        this.setState({
          inspectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  getConnectionResults(page) {
    const { scan, getConnectionScanResults } = this.props;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: 'failed'
    };

    getConnectionScanResults(scan.most_recent.id, queryObject)
      .then(results => {
        const morePages = _.get(results.value, 'data.next') !== null;
        this.setState({
          connectionScanResultsPending: morePages,
          scanResults: this.addResults(results)
        });

        if (morePages) {
          this.getConnectionResults(page + 1);
        }
      })
      .catch(error => {
        this.setState({
          connectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  refresh() {
    this.setState({ scanResultsPending: true, inspectionScanResultsPending: true, scanResults: [] });
    this.getConnectionResults(1);
    this.getInspectionResults(1);
  }

  render() {
    const { scanResults, connectionScanResultsPending, inspectionScanResultsPending, scanResultsError } = this.state;

    if (connectionScanResultsPending || inspectionScanResultsPending) {
      return (
        <EmptyState>
          <EmptyState.Icon name="spinner spinner-xl" />
          <EmptyState.Title>Loading scan results...</EmptyState.Title>
        </EmptyState>
      );
    }

    if (scanResultsError) {
      return (
        <EmptyState>
          <EmptyState.Icon name="error-circle-o" />
          <EmptyState.Title>Error retrieving scan results</EmptyState.Title>
          <EmptyState.Info>{scanResultsError}</EmptyState.Info>
        </EmptyState>
      );
    }

    if (_.size(scanResults) === 0) {
      return (
        <EmptyState>
          <EmptyState.Icon name="warning-triangle-o" />
          <EmptyState.Title>
            {`${helpers.scanStatusString('failed')} systems were not available, please refresh.`}
          </EmptyState.Title>
        </EmptyState>
      );
    }

    return (
      <Grid fluid className="host-list">
        {scanResults &&
          scanResults.map((host, index) => (
            <Grid.Row key={index}>
              <Grid.Col xs={6} sm={4}>
                <span>
                  <Icon type="pf" name="error-circle-o" />
                  &nbsp; {host.name}
                </span>
              </Grid.Col>
            </Grid.Row>
          ))}
      </Grid>
    );
  }
}

ScanFailedHostList.propTypes = {
  scan: PropTypes.object,
  lastRefresh: PropTypes.number,
  getConnectionScanResults: PropTypes.func,
  getInspectionScanResults: PropTypes.func
};

const mapStateToProps = function(state) {
  return {};
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getConnectionScanResults: (id, query) => dispatch(getConnectionScanResults(id, query)),
  getInspectionScanResults: (id, query) => dispatch(getInspectionScanResults(id, query))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanFailedHostList);
