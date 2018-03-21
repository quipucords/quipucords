import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import { EmptyState, Grid, Icon, Pager } from 'patternfly-react';
import { getConnectionScanResults, getInspectionScanResults } from '../../redux/actions/scansActions';

class ScanHostList extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['onNextPage', 'onPreviousPage']);

    this.state = {
      scanResults: [],
      scanResultsError: false,
      connectionScanResultsPending: false,
      inspectionScanResultsPending: false,
      page: 1,
      disableNext: true,
      disablePrevious: true
    };
  }

  componentDidMount() {
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh) || nextProps.status !== this.props.status) {
      this.refresh(nextProps.status);
    }
  }

  onNextPage() {
    this.setState({ page: this.state.page + 1 });
    this.refresh(this.state.page + 1);
  }

  onPreviousPage() {
    this.setState({ page: this.state.page - 1 });
    this.refresh(this.state.page - 1);
  }

  addResults(results) {
    const { scanResults } = this.state;
    const { status } = this.props;

    let statusResults = [];
    _.forEach(_.get(results, 'value.data.results', []), result => {
      if (result.status === status) {
        statusResults.push(result);
      }
    });

    let allResults = [...scanResults, ...statusResults];

    allResults.sort((item1, item2) => {
      if (helpers.isIpAddress(item1.name) && helpers.isIpAddress(item2.name)) {
        const value1 = helpers.ipAddressValue(item1.name);
        const value2 = helpers.ipAddressValue(item2.name);

        return value1 - value2;
      }

      return item1.name.localeCompare(item2.name);
    });

    return allResults;
  }

  getInspectionResults(page, status) {
    const { scan, getInspectionScanResults } = this.props;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: status
    };

    getInspectionScanResults(scan.most_recent.id, queryObject)
      .then(results => {
        // At the moment, we are getting all results
        const morePages = _.get(results.value, 'data.next') !== null;

        this.setState({
          inspectionScanResultsPending: morePages,
          scanResults: this.addResults(results)
        });

        if (morePages) {
          this.getInspectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          inspectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  getConnectionResults(page, status) {
    const { scan, getConnectionScanResults } = this.props;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: status
    };

    getConnectionScanResults(scan.most_recent.id, queryObject)
      .then(results => {
        const morePages = _.get(results.value, 'data.next') !== null;
        this.setState({
          connectionScanResultsPending: morePages,
          scanResults: this.addResults(results)
        });

        if (morePages) {
          this.getConnectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          connectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  refresh(propStatus) {
    const status = propStatus || this.props.status;
    const getConnectionResults = status === 'failed';

    this.setState({
      scanResultsPending: true,
      connectionScanResultsPending: getConnectionResults,
      inspectionScanResultsPending: true,
      scanResults: []
    });

    if (getConnectionResults) {
      this.getConnectionResults(1, status);
    }

    this.getInspectionResults(1, status);
  }

  render() {
    const { status } = this.props;
    const {
      scanResults,
      connectionScanResultsPending,
      inspectionScanResultsPending,
      scanResultsError,
      disablePrevious,
      disableNext
    } = this.state;

    if (inspectionScanResultsPending || connectionScanResultsPending) {
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
            {`${helpers.scanStatusString(status)} systems were not available, please refresh.`}
          </EmptyState.Title>
        </EmptyState>
      );
    }

    return (
      <React.Fragment>
        {(!disableNext || !disablePrevious) && (
          <Grid fluid>
            <Grid.Row>
              <Pager
                className="pager-sm"
                onNextPage={this.onNextPage}
                onPreviousPage={this.onPreviousPage}
                disableNext={disableNext}
                disablePrevious={disablePrevious}
              />
            </Grid.Row>
          </Grid>
        )}
        <Grid fluid className="host-list">
          {scanResults &&
            scanResults.map((host, index) => (
              <Grid.Row key={index}>
                <Grid.Col xs={6} sm={4}>
                  <span>
                    <Icon type="pf" name={host.status === 'success' ? 'ok' : 'error-circle-o'} />
                    &nbsp; {host.name}
                  </span>
                </Grid.Col>
              </Grid.Row>
            ))}
        </Grid>
      </React.Fragment>
    );
  }
}

ScanHostList.propTypes = {
  scan: PropTypes.object,
  lastRefresh: PropTypes.number,
  status: PropTypes.string,
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

export default connect(mapStateToProps, mapDispatchToProps)(ScanHostList);
